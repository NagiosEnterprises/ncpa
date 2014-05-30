import os
import tempfile
import time
import itertools
import logging
import pickle
import re


class ParentNode(object):

    def __init__(self, name, children, *args, **kwargs):
        self.children = children
        self.children_names = [x.name for x in children]
        self.name = name

    def accessor(self, path, config):
        if path:
            next_child_name, rest_path = path[0], path[1:]
            child_index = self.children_names.index(next_child_name)
            child = self.children[child_index]
            return child.accessor(rest_path, config)
        else:
            return self

    def walk(self, *args, **kwargs):
        stat = {}
        for child in self.children:
            try:
                if kwargs.get('first', None) is None:
                    kwargs['first'] = False
                stat.update(child.walk(*args, **kwargs))
            except Exception as exc:
                stat.update({child.name: 'Error retrieving child: %r' % str(exc)})
        return {self.name: stat}

    def run_check(self, *args, **kwargs):
        return {'stdout': 'Unable to run check on non-child node. Revise your query.',
                'returncode': 3}


class RunnableNode(ParentNode):

    def __init__(self, name, method, *args, **kwargs):
        self.method = method
        self.name = name
        self.children = []
        self.unit = ''

    def accessor(self, path, config):
        if path:
            raise IndexError('End of path node called with more path')
        else:
            return self

    def walk(self, *args, **kwargs):
        result = self.method()
        return {self.name: result}

    def run_check(self, *args, **kwargs):
        values, self.unit = self.method()
        if not isinstance(values, (list, tuple)):
            values = [values]

        delta = kwargs.get('delta', False)
        accessor = kwargs.get('accessor', None)
        if delta:
            values = self.deltaize_values(values, accessor)

        units = kwargs.get('units', None)
        if not units is None:
            values, units = self.adjust_scale(values, units[0])
            self.unit = '%s%s' % (units, self.unit)

        try:
            warning, is_warning = kwargs.get('warning', ''), False
            critical, is_critical = kwargs.get('critical', ''), False
            if warning:
                warning = warning[0]
                is_warning = any([self.is_within_range(warning, x) for x in values])
            if critical:
                critical = critical[0]
                is_critical = any([self.is_within_range(critical, x) for x in values])
            returncode, stdout = self.get_nagios_return(values, is_warning, is_critical, warning, critical, delta)
        except Exception as exc:
            returncode = 3
            stdout = str(exc)
            logging.exception(exc)

        return {'returncode': returncode, 'stdout': stdout}

    def get_nagios_return(self, values, is_warning, is_critical, warning='', critical='', delta=False):
        proper_name = self.name.title().replace('|', '/')

        if delta:
            nice_unit = '%s/sec' % self.unit
        else:
            nice_unit = '%s' % self.unit

        nice_values = []
        for x in values:
            nice_values.append('%d%s' % (x, nice_unit))
        values_for_info_line = ','.join(nice_values)

        returncode = 0
        info_prefix = 'OK'

        if is_warning:
            returncode = 1
            info_prefix = 'WARNING'
        if is_critical:
            returncode = 2
            info_prefix = 'CRITICAL'

        perfdata_label = self.name.replace(' ', '_').replace("'", '"')
        perfdata = []
        for i, x in enumerate(values):
            perf = "'%s_%d'=%d%s;%s;%s;" % (self.name, i, x, self.unit, warning, critical)
            perfdata.append(perf)
        perfdata = ' '.join(perfdata)

        info_line = '%s: %s was %s' % (info_prefix, proper_name, values_for_info_line)
        stdout = '%s | %s' % (info_line, perfdata)

        return returncode, stdout

    @staticmethod
    def deltaize_values(values, accessor):
        filename = "ncpa-%d.tmp" % hash(accessor)
        tmpfile = os.path.join(tempfile.gettempdir(), filename)

        try:
            #If the file exists, we extract the data from it and save it to our loaded_values
            #variable.
            with open(tmpfile, 'r') as values_file:
                loaded_values = pickle.load(values_file)
                last_modified = os.path.getmtime(tmpfile)
        except (IOError, EOFError):
            #Otherwise load the loaded_values and last_modified with values that will cause zeros
            #to show up.
            logging.info('No pickle file found for accessor %s' % accessor)
            loaded_values = values
            last_modified = 0

        #Update the pickled data
        logging.debug('Updating pickle for %s. Filename is %s.' % (accessor, tmpfile))
        with open(tmpfile, 'w') as values_file:
            pickle.dump(values, values_file)

        #Calcluate the return value and return it
        delta = time.time() - last_modified
        return [abs((x - y) / delta) for x, y in itertools.izip(loaded_values, values)]

    @staticmethod
    def adjust_scale(values, units):
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
        result = []
        if kwargs.get('first', True):
            result = self.method()
        return {self.name: result}
