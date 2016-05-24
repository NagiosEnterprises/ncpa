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


class RunnableParentNode(ParentNode):

    def __init__(self, name, children, primary, include=None, *args, **kwargs):
        super(RunnableParentNode, self).__init__(name, children)
        self.primary = primary
        if include is None:
            self.include = [x for x in self.children]
        else:
            self.include = include

    def run_check(self, *args, **kwargs):
        primary_info = {}
        secondary_results = []
        for name, child in self.children.iteritems():
            if name in self.include:
                if name == self.primary:
                    primary_info  = child.run_check(use_prefix=True, use_perfdata=True,
                                                    primary=True, *args, **kwargs)
                else:
                    result = child.run_check(use_prefix=False, use_perfdata=False,
                                             primary=False, *args, **kwargs)
                    stdout = result.get('stdout', None)
                    secondary_results.append(stdout)
        secondary_stdout = ' -- '.join(x for x in secondary_results if x)
        primary_info['stdout'] = primary_info['stdout'].format(extra_data=secondary_stdout)
        return primary_info


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
        values = self.get_aggregated_values(values, kwargs)

        if self.unit != '':
            return {self.name: [values, self.unit]}

        return {self.name: values}

    def set_unit(self, unit, request_args):
        if 'unit' in request_args:
            self.unit = request_args['unit'][0]
        else:
            self.unit = unit

    def get_delta_values(self, values, request_args, hasher=False):
        delta = request_args.get('delta', False)
        # Here we check which value we should hash against for the delta pickle
        # If the value is empty string, empty list, empty object, 0, False or None,
        # then this is clearly not what we want and we simply hash against the API
        # accessor.
        if not hasher:
            accessor = request_args.get('accessor', None)
        else:
            accessor = hasher

        if delta:
            self.delta = True
            values = self.deltaize_values(values, accessor)
        return values

    def get_adjusted_scale(self, values, request_args):
        units = request_args.get('units', None)
        if units is not None and self.unit in ['b', 'B']:
            values, units = self.adjust_scale(self, values, units[0])
        return values

    def set_warning(self, request_args):
        warning = request_args.get('warning', '')
        self.warning = warning

    def set_critical(self, request_args):
        critical = request_args.get('critical', '')
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

    def get_aggregated_values(self, values, request_args):
        aggregate = request_args.get('aggregate', 'None')
        
        # Do a quick check to verify that we are using a string not a list/tuple
        # which happens to occur on Windows requests only...
        if isinstance(aggregate, (list, tuple)):
            aggregate = aggregate[0]
        
        if aggregate == 'max':
            print 'Doing max'
            return [max(values)]
        elif aggregate == 'min':
            return [min(values)]
        elif aggregate == 'sum':
            return [sum(values)]
        elif aggregate == 'avg':
            return [sum(values) / len(values)]
        else:
            return values

    def run_check(self, use_perfdata=True, use_prefix=True, primary=False, *args, **kwargs):
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
            values = self.get_aggregated_values(values, kwargs)
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
            returncode, stdout = self.get_nagios_return(values, is_warning, is_critical, use_perfdata, use_prefix, primary)
        except Exception as exc:
            returncode = 3
            stdout = str(exc)
            logging.exception(exc)

        return { 'returncode': returncode, 'stdout': stdout }

    def get_nagios_return(self, values, is_warning, is_critical, use_perfdata=True, use_prefix=True, primary=False):
        proper_name = self.title.replace('|', '/')

        if self.delta:
            nice_unit = '%s/sec' % self.unit
        else:
            nice_unit = '%s' % self.unit

        if not isinstance(values, (list, tuple)):
            values = [values]

        nice_values = []
        for x in values:
            try:
                nice_values.append('%d %s' % (x, nice_unit))
            except TypeError:
                logging.info('Did not receive normal values. Unable to find meaningful check.')
                return 0, 'OK: %s was %s' % (str(proper_name).capitalize(), str(values))
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

        if isinstance(self.warning, list):
            self.warning = self.warning[0]

        if isinstance(self.critical, list):
            self.critical = self.critical[0]

        perfdata = []
        for i, x in enumerate(values):
            perf = "'%s_%d'=%d%s;%s;%s;" % (perfdata_label, i, x, perf_unit, self.warning, self.critical)
            perfdata.append(perf)
        perfdata = ' '.join(perfdata)

        stdout = '%s was %s' % (proper_name.capitalize(), values_for_info_line)

        if use_prefix is True:
            stdout = '%s: %s' % (info_prefix, stdout)

        if primary is True:
            stdout = '%s -- {extra_data}' % stdout

        if use_perfdata is True:
            stdout = '%s | %s' % (stdout, perfdata)

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
        except (KeyError, pickle.UnpicklingError):
            logging.info('Problem unpickling data for accessor %s', accessor)
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
    def adjust_scale(self, values, units):

        # It was either adjust it here or adjust every single node that only returns a single value. I'm putting this
        # on the TODO for 2.0 to change all nodes to return lists rather than single values, as thats a API breaking
        # change.
        if not isinstance(values, (list, tuple)):
            values = [values]

        units = units.upper()
        factor = 1.0

        if units in ['G', 'M', 'K']:
            if units == 'T':
                factor = 1e12
            elif units == 'G':
                factor = 1e9
            elif units == 'M':
                factor = 1e6
            elif units == 'K':
                units = 'k'
                factor = 1e3
            else:
                factor = 1.0
        elif units in ['TI', 'GI', 'MI', 'KI']:
            if units == 'TI':
                units = 'Ti'
                factor = 1.074e12
            elif units == 'GI':
                units = 'Gi'
                factor = 1.074e9
            elif units == 'MI':
                units = 'Mi'
                factor = 1.074e6
            elif units == 'KI':
                units = 'Ki'
                factor = 1.074e3

        values = [round(x/factor, 2) for x in values]

        if factor != 1.0:
            self.unit = '%s%s' % (units, self.unit)

        return values, units

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
        nagios_range = ''.join(nagios_range)
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
