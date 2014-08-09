import os
import tempfile
import time
import itertools
import logging
import pickle
import copy
import re


class ParentNode(object):

    def __init__(self, name, children=None, *args, **kwargs):
        if children is None:
            children = []

        self.children = {}
        self.name = name
        for child in children:
            self.add_child(child)

    def add_child(self, new_node):
        self.children[new_node.name] = new_node

    def accessor(self, path, config):
        if path:
            next_child_name, rest_path = path[0], path[1:]
            try:
                child = self.children[next_child_name]
            except KeyError:
                child = ERROR_NODE
            return child.accessor(rest_path, config)
        else:
            return copy.deepcopy(self)

    def walk(self, *args, **kwargs):
        stat = {}
        for name, child in self.children.iteritems():
            try:
                if kwargs.get('first', None) is None:
                    kwargs['first'] = False
                stat.update(child.walk(*args, **kwargs))
            except Exception as exc:
                logging.exception(exc)
                stat.update({name: 'Error retrieving child: %r' % str(exc)})
        return {self.name: stat}

    def run_check(self, *args, **kwargs):
        return {'stdout': 'Unable to run check on non-child node. Revise your query.',
                'returncode': 3}

ERROR_NODE = ParentNode(name='NodeDoesNotExist', children=[])


class RunnableNode(ParentNode):

    def __init__(self, name, method, *args, **kwargs):
        self.method = method
        self.name = name
        self.children = {}
        self.unit = ''
        self.delta = False

    def accessor(self, path, config):
        if path:
            raise IndexError('End of path node called with more path')
        else:
            return copy.deepcopy(self)

    def walk(self, *args, **kwargs):
        try:
            values, unit = self.method(*args, **kwargs)
        except TypeError:
            values, unit = self.method()
        self.set_unit(unit, kwargs)
        values = self.get_adjusted_scale(values, kwargs)
        values = self.get_delta_values(values, kwargs)
        return {self.name: [values, self.unit]}

    def set_unit(self, unit, request_args):
        if 'unit' in request_args:
            self.unit = request_args['unit'][0]
        else:
            self.unit = unit

    def get_delta_values(self, values, request_args, hasher=False):
        delta = request_args.get('delta', False)
        if hasher is None:
            accessor = request_args.get('accessor', None)
        else:
            accessor = hasher
        if delta:
            self.delta = True
            values = self.deltaize_values(values, accessor)
        return values

    def get_adjusted_scale(self, values, request_args):
        units = request_args.get('units', None)
        if units is not None:
            values, units = self.adjust_scale(values, units[0])
            self.unit = '%s%s' % (units, self.unit)
        return values

    def set_warning(self, request_args):
        warning = request_args.get('warning', '')
        if warning:
            self.warning = warning[0]
        else:
            self.warning = warning

    def set_critical(self, request_args):
        critical = request_args.get('critical', '')
        if critical:
            self.critical = critical[0]
        else:
            self.critical = critical

    def set_title(self, request_args):
        title = request_args.get('title', None)
        if not title is None:
            self.title = title[0]
        else:
            self.title = self.name

    def set_perfdata_label(self, request_args):
        perfdata_label = request_args.get('perfdata_label', None)
        if not perfdata_label is None:
            self.perfdata_label = perfdata_label[0]
        else:
            self.perfdata_label = None

    def run_check(self, *args, **kwargs):
        try:
            values, unit = self.method(*args, **kwargs)
        except TypeError:
            values, unit = self.method()
        except AttributeError:
            return self.execute_plugin(*args, **kwargs)

        if not isinstance(values, (list, tuple)):
            values = [values]

        self.set_unit(unit, kwargs)
        self.set_title(kwargs)
        self.set_perfdata_label(kwargs)
        try:
            values = self.get_delta_values(values, kwargs)
            values = self.get_adjusted_scale(values, kwargs)
        except TypeError:
            logging.warning('Error converting values to scale and delta. Values: %r' % values)

        try:
            self.set_warning(kwargs)
            self.set_critical(kwargs)
            is_warning = False
            is_critical = False
            if self.warning:
                is_warning = any([self.is_within_range(self.warning, x) for x in values])
            if self.critical:
                is_critical = any([self.is_within_range(self.critical, x) for x in values])
            returncode, stdout = self.get_nagios_return(values, is_warning, is_critical)
        except Exception as exc:
            returncode = 3
            stdout = str(exc)
            logging.exception(exc)

        return {'returncode': returncode, 'stdout': stdout}

    def get_nagios_return(self, values, is_warning, is_critical):
        proper_name = self.title.replace('|', '/')

        if self.delta:
            nice_unit = '%s/sec' % self.unit
        else:
            nice_unit = '%s' % self.unit

        nice_values = []
        for x in values:
            try:
                nice_values.append('%d%s' % (x, nice_unit))
            except TypeError:
                logging.warning('Did not receive normal values. Unable to find meaningful check.')
                return '%s was %s' % (str(proper_name), str(values)), 0
        values_for_info_line = ','.join(nice_values)

        returncode = 0
        info_prefix = 'OK'

        if is_warning:
            returncode = 1
            info_prefix = 'WARNING'
        if is_critical:
            returncode = 2
            info_prefix = 'CRITICAL'

        if self.perfdata_label is None:
            perfdata_label = self.title.replace('=', '_').replace("'", '"')
        else:
            perfdata_label = self.perfdata_label

        if len(self.unit) > 2:
            perf_unit = ''
        else:
            perf_unit = self.unit

        perfdata = []
        for i, x in enumerate(values):
            perf = "'%s_%d'=%d%s;%s;%s;" % (perfdata_label, i, x, perf_unit, self.warning, self.critical)
            perfdata.append(perf)
        perfdata = ' '.join(perfdata)

        info_line = '%s: %s was %s' % (info_prefix, proper_name, values_for_info_line)
        stdout = '%s | %s' % (info_line, perfdata)

        return returncode, stdout

    @staticmethod
    def deltaize_values(values, accessor):
        filename = "ncpa-%d.tmp" % hash(accessor)
        tmpfile = os.path.join(tempfile.gettempdir(), filename)

        if not isinstance(values, (list, tuple)):
            values = [values]

        try:
            #If the file exists, we extract the data from it and save it to our loaded_values
            #variable.
            with open(tmpfile, 'r') as values_file:
                loaded_values = pickle.load(values_file)
                last_modified = os.path.getmtime(tmpfile)
        except (IOError, EOFError):
            #Otherwise load the loaded_values and last_modified with values that will cause zeros
            #to show up.
            logging.info('No pickle file found for accessor %s', accessor)
            loaded_values = values
            last_modified = 0

        #Update the pickled data
        logging.debug('Updating pickle for %s. Filename is %s.', accessor, tmpfile)
        with open(tmpfile, 'w') as values_file:
            pickle.dump(values, values_file)

        #Calculate the return value and return it
        delta = time.time() - last_modified
        return [abs((x - y) / delta) for x, y in itertools.izip(loaded_values, values)]

    @staticmethod
    def adjust_scale(values, units):

        # It was either adjust it here or adjust every single node that only returns a single value. I'm putting this
        # on the TODO for 2.0 to change all nodes to return lists rather than single values, as thats a API breaking
        # change.
        if not isinstance(values, (list, tuple)):
            values = [values]

        units = units.upper()
        if units == 'G':
            factor = 1e9
        elif units == 'M':
            factor = 1e6
        elif units == 'K':
            factor = 1e3
        else:
            factor = 1.0

        return [x/factor for x in values], units

    @staticmethod
    def is_within_range(nagios_range, value):
        """Returns True if the given value will raise an alert for the given
        nagios_range.

        """
        #First off, we must ensure that the range exists, otherwise just return (not warning or critical.)
        if not nagios_range:
            return False

        #Next make sure the value is a number of some sort
        value = float(value)

        #Setup our regular expressions to parse the Nagios ranges
        first_float = r'(?P<first>(-?[0-9]+(\.[0-9]+)?))'
        second_float = r'(?P<second>(-?[0-9]+(\.[0-9]+)?))'

        #The following is a list of regular expression => function. If the regular expression matches
        #then run the function. The function is a comparison involving value.
        actions = [(r'^%s$' % first_float, lambda y: (value > float(y.group('first'))) or (value < 0)),
                   (r'^%s:$' % first_float, lambda y: value < float(y.group('first'))),
                   (r'^~:%s$' % first_float, lambda y: value > float(y.group('first'))),
                   (r'^%s:%s$' % (first_float, second_float), lambda y: (value < float(y.group('first'))) or (value > float(y.group('second')))),
                   (r'^@%s:%s$' % (first_float, second_float), lambda y: not((value < float(y.group('first'))) or (value > float(y.group('second')))))]

        #For each of the previous list items, run the regular expression, and if the regular expression
        #finds a match, run the function and return its comparison result.
        for regex_string, func in actions:
            res = re.match(regex_string, nagios_range)
            if res:
                return func(res)

        #If none of the items matches, the warning/critical format was bogus! Sound the alarms!
        raise Exception('Improper warning/critical format.')


class LazyNode(RunnableNode):

    def walk(self, *args, **kwargs):
        if kwargs.get('first', True):
            return super(LazyNode, self).walk(*args, **kwargs)
        else:
            return {self.name: []}
