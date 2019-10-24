import os
import tempfile
import time
import itertools
import logging
import pickle
import copy
import re
import database
import server
import ConfigParser
from datetime import datetime, timedelta


# Valid nodes is updated as it gets set when calling a node via accessor
valid_nodes = []


class ParentNode(object):

    def __init__(self, name, children=None, *args, **kwargs):
        if children is None:
            children = []

        self.children = {}
        self.name = name

        for child in children:
            self.add_child(child)

    def reset_valid_nodes(self):
        global valid_nodes
        valid_nodes = []

    def add_child(self, new_node):
        self.children[new_node.name] = new_node

    def accessor(self, path, config, full_path, args):
        if path:
            next_child_name, rest_path = path[0], path[1:]
            try:
                child = self.children[next_child_name]
                valid_nodes.append(next_child_name)
            except KeyError:
                # Record all proper valid nodes
                for child in self.children:
                    valid_nodes.append(child)

                # Create a does not exist node to return error message
                if self.__class__.__name__ == 'PluginAgentNode':
                    return DoesNotExistNode(next_child_name, 'plugin', full_path)
                return DoesNotExistNode(next_child_name, 'node', full_path)

            # Continue down the node path
            return child.accessor(rest_path, config, full_path, args)
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
                stat.update({ name: 'Error retrieving child: %r' % str(exc) })
        return { self.name: stat }

    def run_check(self, *args, **kwargs):
        err = 'UNKNOWN: Unable to run check on node without check method. Requested \'%s\' node.' % self.name
        return { 'stdout': err,
                 'returncode': 3 }


class RunnableParentNode(ParentNode):

    def __init__(self, name, children, primary, primary_unit='',
                 custom_output=None, include=None, *args, **kwargs):
        super(RunnableParentNode, self).__init__(name, children)
        self.primary = primary
        self.primary_unit = primary_unit
        self.custom_output = custom_output
        if include is None:
            self.include = [x for x in self.children]
        else:
            self.include = include

    def run_check(self, *args, **kwargs):
        primary_info = {}
        secondary_results = []
        secondary_perfdata = []
        total = ''

        if self.primary_unit == '%':
            total, total_unit = self.children['total'].get_values(*args, **kwargs)
            total = total[0]

        for name, child in self.children.iteritems():
            if name in self.include:
                if name == self.primary:
                    primary_info  = child.run_check(use_prefix=True,
                                                    use_perfdata=False,
                                                    primary=True,
                                                    secondary_data=False,
                                                    custom_output=self.custom_output,
                                                    child_check=True,
                                                    *args, **kwargs)
                else:
                    result = child.run_check(use_prefix=False, use_perfdata=False,
                                             primary=False, primary_total=total,
                                             secondary_data=True,
                                             child_check=True, *args, **kwargs)
                    stdout = result.get('stdout', None)
                    if stdout is not None:
                        secondary_results.append(stdout)

                    # Add perfdata if it exists
                    perfdata = result.get('perfdata', None)
                    if perfdata is not None:
                        secondary_perfdata.append(perfdata)

        secondary_stdout = '(' + ', '.join(x for x in secondary_results if x) + ')'
        primary_info['stdout'] = primary_info['stdout'].format(extra_data=secondary_stdout)

        # Add extra perfdata on (if it exists)
        if secondary_perfdata:
            extra_perfdata = ''
            if self.primary_unit != '%':
                extra_perfdata += primary_info['perfdata'] + ' '
            extra_perfdata += ' '.join(secondary_perfdata)
            primary_info['stdout'] = primary_info['stdout'] + ' | ' + extra_perfdata

        # Remove perfdata from actual check data sent out
        del primary_info['perfdata']

        # Get the check logging value
        try:
            check_logging = int(kwargs['config'].get('general', 'check_logging'))
        except Exception as e:
            check_logging = 1

        # Send check results to database
        if not server.__INTERNAL__ and check_logging == 1:
            db = database.DB()
            current_time = time.time()
            db.add_check(kwargs['accessor'].rstrip('/'), current_time, current_time, primary_info['returncode'],
                         primary_info['stdout'], kwargs['remote_addr'], 'Active')

        return primary_info


class RunnableNode(ParentNode):

    def __init__(self, name, method, *args, **kwargs):
        self.method = method
        self.name = name
        self.children = {}
        self.unit = ''
        self.delta = False

    def accessor(self, path, config, full_path, args):
        if path:
            full_path = ', '.join(path)
            return DoesNotExistNode('', self.name, full_path)
        else:
            return copy.deepcopy(self)

    def walk(self, *args, **kwargs):
        try:
            values, unit = self.method(*args, **kwargs)
        except TypeError:
            values, unit = self.method()

        self.set_unit(unit, kwargs)
        values = self.get_adjusted_scale(values, kwargs)
        values = self.get_delta_values(values, kwargs, *args, **kwargs)
        values = self.get_aggregated_values(values, kwargs)

        if self.unit != '':
            return { self.name: [values, self.unit] }
        return { self.name: values }

    def set_unit(self, unit, request_args):
        if 'unit' in request_args:
            self.unit = request_args['unit'][0]
        else:
            self.unit = unit

    def get_delta_values(self, values, request_args, hasher=False, *args, **kwargs):
        delta = request_args.get('delta', False)
        # Here we check which value we should hash against for the delta pickle
        # If the value is empty string, empty list, empty object, 0, False or None,
        # then this is clearly not what we want and we simply hash against the API
        # accessor.
        if not hasher:
            accessor = request_args.get('accessor', '')
        else:
            accessor = hasher

        # Make accessor even more unique (for parent node deltas)
        accessor += '.' + self.name

        if delta:
            self.delta = True
            self.unit = self.unit + '/s'
            remote_addr = request_args.get('remote_addr', None)

            values = self.deltaize_values(values, accessor, remote_addr)

            # Wait 1 second and try again if no value was given due to no pickle
            # file having been created yet (check doesn't have old data)
            if values is False:
                time.sleep(1)
                logging.debug('Re-running check for 1 second of data.')
                try:
                    values, unit = self.method(*args, **kwargs)
                except TypeError:
                    values, unit = self.method()
                values = self.deltaize_values(values, accessor, remote_addr)

        return values

    def get_adjusted_scale(self, values, request_args):
        units = request_args.get('units', None)
        if units is not None and self.unit in ['b', 'B']:
            values, units = self.adjust_scale(self, values, units)
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
            return [max(values)]
        elif aggregate == 'min':
            return [min(values)]
        elif aggregate == 'sum':
            return [sum(values)]
        elif aggregate == 'avg':
            return [round(sum(values) / len(values), 2)]
        else:
            return values

    def get_values(self, *args, **kwargs):
        try:
            values, unit = self.method(*args, **kwargs)
        except TypeError:
            values, unit = self.method()

        self.set_unit(unit, kwargs)
        self.set_title(kwargs)
        self.set_perfdata_label(kwargs)
        try:
            values = self.get_adjusted_scale(values, kwargs)
            values = self.get_delta_values(values, kwargs)
            values = self.get_aggregated_values(values, kwargs)
        except TypeError:
            logging.warning('Error converting values to scale and delta. Values: %r' % values)

        if not isinstance(values, (list, tuple)):
            values = [values]

        return values, unit

    def run_check(self, use_perfdata=True, use_prefix=True, primary=False,
                  primary_total=0, secondary_data=False, custom_output=None,
                  capitalize=True, child_check=False, *args, **kwargs):
        
        try:
            values, unit = self.get_values(*args, **kwargs)
        except AttributeError:
            return self.execute_plugin(*args, **kwargs)

        try:
            self.set_warning(kwargs)
            self.set_critical(kwargs)
            is_warning = False
            is_critical = False
            if self.warning:
                is_warning = any([self.is_within_range(self.warning, x) for x in values])
            if self.critical:
                is_critical = any([self.is_within_range(self.critical, x) for x in values])
            returncode, stdout, perfdata = self.get_nagios_return(values, is_warning, is_critical, use_perfdata,
                                                use_prefix, primary, primary_total, secondary_data,
                                                custom_output, capitalize)
        except Exception as exc:
            returncode = 3
            stdout = str(exc)
            logging.exception(exc)

        # Get the check logging value
        try:
            check_logging = int(kwargs['config'].get('general', 'check_logging'))
        except Exception as e:
            check_logging = 1

        # Send check results to database
        if not child_check and not server.__INTERNAL__ and check_logging == 1:
            db = database.DB()
            current_time = time.time()
            db.add_check(kwargs['accessor'].rstrip('/'), current_time, current_time, returncode,
                         stdout, kwargs['remote_addr'], 'Active')

        data = { 'returncode': returncode, 'stdout': stdout }
        if child_check:
            data['perfdata'] = perfdata

        return data

    def get_nagios_return(self, values, is_warning, is_critical, use_perfdata=True,
                          use_prefix=True, primary=False, primary_total=0, secondary_data=False,
                          custom_output=None, capitalize=True):

        proper_name = self.title.replace('|', '/')

        if capitalize:
            proper_name = proper_name.capitalize()

        if not isinstance(values, (list, tuple)):
            values = [values]

        nice_values = []
        for x in values:
            try:
                if isinstance(x, int):
                    nice_values.append('%d %s' % (x, self.unit))
                else:
                    nice_values.append('%0.2f %s' % (x, self.unit))
            except TypeError:
                logging.info('Did not receive normal values. Unable to find meaningful check.')
                return 0, 'OK: %s was %s' % (proper_name, str(values)), ''
        values_for_info_line = ', '.join(nice_values)

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

        if len(self.unit) > 3:
            perf_unit = ''
        else:
            perf_unit = self.unit

        if isinstance(self.warning, list):
            self.warning = self.warning[0]

        if isinstance(self.critical, list):
            self.critical = self.critical[0]

        # For a % based parent check we should get the values in the checks
        # base type (normally GiB or B)
        if primary_total:
            if self.warning:
                self.warning = int(round(primary_total * (float(self.warning) / 100)))
            if self.critical:
                self.critical = int(round(primary_total * (float(self.critical) / 100)))

        perfdata = []
        v = len(values)
        for i, x in enumerate(values):

            if isinstance(x, (int, long)):
                perf = "=%d%s;%s;%s;" % (x, perf_unit, self.warning, self.critical)
            else: 
                perf = "=%0.2f%s;%s;%s;" % (x, perf_unit, self.warning, self.critical)

            if v == 1:
                perf = "'%s'%s" % (perfdata_label, perf)
            else:
                perf = "'%s_%d'%s" % (perfdata_label, i, perf)

            perfdata.append(perf)
        
        perfdata = ' '.join(perfdata)

        # Hack in the uptime change because we can't do much else...
        # this will be removed in NCPA 3
        if self.name == 'uptime':
            custom_output = proper_name + ' was ' + self.elapsed_time(values[0])
            values_for_info_line = ''

        if secondary_data is True:
            stdout = '%s: %s' % (proper_name, values_for_info_line)
        else:
            output = proper_name + ' was'
            if custom_output:
                output = custom_output
            stdout = '%s %s' % (output, values_for_info_line)
        stdout = stdout.rstrip()

        if use_prefix is True:
            stdout = '%s: %s' % (info_prefix, stdout)

        if primary is True:
            stdout = '%s {extra_data}' % stdout

        if use_perfdata is True:
            stdout = '%s | %s' % (stdout, perfdata)

        return returncode, stdout, perfdata

    def deltaize_values(self, values, hash_val, remote_addr=None):
        if remote_addr:
            hash_val = hash_val + remote_addr
        filename = "ncpa-%d.tmp" % hash(hash_val)
        tmpfile = os.path.join(tempfile.gettempdir(), filename)

        if not isinstance(values, (list, tuple)):
            values = [values]

        try:
            # If the file exists, we extract the data from it and save it to our loaded_values variable.
            with open(tmpfile, 'r') as values_file:
                loaded_values = pickle.load(values_file)
                last_modified = os.path.getmtime(tmpfile)
        except (IOError, EOFError):
            # Otherwise load the loaded_values and last_modified with values that will cause zeros to show up.
            logging.debug('No pickle file found for hash_val "%s"', hash_val)
            loaded_values = values
            last_modified = 0
        except (KeyError, pickle.UnpicklingError):
            logging.error('Problem unpickling data for hash_val "%s"', hash_val)
            loaded_values = values
            last_modified = 0

        # Update the pickled data
        logging.debug('Updating pickle for hash_val "%s". Filename is %s.', hash_val, tmpfile)
        with open(tmpfile, 'w') as values_file:
            pickle.dump(values, values_file)

        # If last modified is 0, then return false
        if last_modified == 0:
            return 0

        # Calculate the return value and return it
        delta = time.time() - last_modified
        dvalues = [round(abs((x - y) / delta), 2) for x, y in itertools.izip(loaded_values, values)]

        if len(dvalues) == 1:
            dvalues = dvalues[0]

        return dvalues

    @staticmethod
    def adjust_scale(self, values, units):

        # Turn into a list for conversion
        if not isinstance(values, (list, tuple)):
            values = [values]

        # Make sure the unit value is a string not a list or tuple
        if isinstance(units, (list, tuple)):
            units = units[0]

        units = units.upper()
        factor = 1.0

        if units in ['T', 'G', 'M', 'K']:
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
                factor = 1.1e12
            elif units == 'GI':
                units = 'Gi'
                factor = 1.074e9
            elif units == 'MI':
                units = 'Mi'
                factor = 1.049e6
            elif units == 'KI':
                units = 'Ki'
                factor = 1.024e3

        # Process the values and put them back into list, also check if
        # the value is just a bytes value - keep as integer
        pvalues = []
        for x in values:
            val = round(x/factor, 2)
            if units == 'B':
                val = int(val)
            pvalues.append(val)

        # Do not return as a list if we only have 1 value to return
        if len(pvalues) == 1:
            pvalues = pvalues[0]

        if factor != 1.0:
            self.unit = '%s%s' % (units, self.unit)

        return pvalues, units

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
                   (r'^:%s$' % first_float, lambda y: (value > float(y.group('first'))) or (value < 0)),
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

    @staticmethod
    def elapsed_time(seconds):
        intervals = (('days', 86400), ('hours', 3600), ('minutes', 60), ('seconds', 1))
        result = []

        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(int(value), name))
        return ' '.join(result)


class LazyNode(RunnableNode):

    def walk(self, *args, **kwargs):
        if kwargs.get('first', True):
            return super(LazyNode, self).walk(*args, **kwargs)
        else:
            return { self.name: [] }


# -----------------------------
# Error related class definitions
# -----------------------------


# If node does not exist, we should give a decent error message with helpful
# information about the name of the node they are trying to find is
class DoesNotExistNode():

    def __init__(self, failed_node_name, node_type, full_path):
        self.failed_node_name = failed_node_name
        self.full_path = full_path
        self.node_type = node_type
        self.extra_message = ''

        # Check if the node is valid
        for node in valid_nodes:
            if self.failed_node_name in node or node in self.failed_node_name:
                self.extra_message = 'You may be trying to access the \'%s\' node.' % node


    def walk(self, *args, **kwargs):
        err = "The %s requested does not exist." % self.node_type
        if self.extra_message:
            err = "%s %s" % (err, self.extra_message)
        obj = {
                    "error" :
                    {
                        "path" : self.full_path,
                        "code" : 100,
                        "message" : err
                    }
                }
        obj['error'][self.node_type] = self.failed_node_name
        return obj

    def run_check(self, *args, **kwargs):
        err = 'UNKNOWN: The %s (%s) requested does not exist.' % (self.node_type, self.failed_node_name)
        if self.extra_message:
            err = "%s %s" % (err, self.extra_message)
        err = err.replace('|', '/')
        return { 'stdout': err,
                 'returncode': 3 }
