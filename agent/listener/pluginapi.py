import subprocess
import os
import ConfigParser
import logging
import shlex
import urlparse
import tempfile
import pickle
import time
import re


def get_cmdline(plugin_name, plugin_args, instruction):
    """Execute with special instructions.
    
    EXAMPLE instruction (Powershell):
    powershell -ExecutionPolicy Unrestricted $plugin_name $plugin_args
    
    EXAMPLE instruction (VBS):
    wscript $plugin_name $plugin_args

    """  
    command = []
    for x in shlex.split(instruction):
        if '$plugin_name' == x:
            command.append(plugin_name)
        elif '$plugin_args' == x and plugin_args:
            for y in plugin_args:
                command.append(y)
        else:
            command.append(x)
    return command


def deltaize_call(key_name, result):
    """Saves the results from this run of the check to be checked later.

    """
    #Get our temp file filename to save our results too.
    filename = "ncpa-%s.tmp" % str(hash(key_name))
    tmpfile = os.path.join(tempfile.gettempdir(), filename)

    if os.path.isfile(tmpfile):
        #If the file exists, we extract the data from it and save it to our loaded_result
        #variable.
        result_file = open(tmpfile, 'r')
        loaded_result = pickle.load(result_file)
        result_file.close()
        last_modified = os.path.getmtime(tmpfile)
    else:
        #Otherwise load the loaded_result and last_modified with values that will cause zeros
        #to show up.
        loaded_result = result
        last_modified = 0

    #Update the pickled data
    logging.debug('Updating pickle for %s. filename is %s.' % (key_name, tmpfile))
    result_file = open(tmpfile, 'w')
    pickle.dump(result, result_file)
    result_file.close()

    #Calcluate the return value and return it
    delta = time.time() - last_modified
    return [abs((x - y) / delta) for x, y in zip(loaded_result, result)]


def make_plugin_response_from_accessor(accessor_response, accessor_args):
    """This function is a monster and needs to be broken up and rewritten

    """
    # TODO: Rewrite this beast.
    #~ First look at the GET and POST arguments to see what we are 
    #~ going to use for our warning/critical
    try:
        processed_args = dict(urlparse.parse_qsl(accessor_args))
    except ValueError:
        logging.debug('No argument detected in string %s' % accessor_args)
        processed_args = {}
    except Exception, e:
        processed_args = {}
        logging.exception(e)
        logging.warning('Unabled to process arguments.')
    
    #~ We need to have [{dictionary: value}] structure, so if it isn't that
    #~ we need to throw a warning
    if type(accessor_response.values()[0]) is dict:
        stdout = 'ERROR: Non-node value requested. Requested entire tree.'
        returncode = 3
    else:
        result = accessor_response.values()[0]
        if not type(result) in [list, tuple]:
            unit = ''
            result = [result]
        try:
            unit = result[1]
        except IndexError:
            unit = ''
        result = result[0]
        
        if type(result) == bool:
            bool_name = accessor_response.keys()[0]
            if result:
                return {'returncode': 0, 'stdout': "%s's status was as expected." % bool_name}
            else:
                return {'returncode': 2, 'stdout': "%s's status was not as expected." % bool_name}
        elif not type(result) in [list, tuple]:
            result = [result]
        
        warning = processed_args.get('warning')
        critical = processed_args.get('critical')
        s_unit = processed_args.get('unit')
        delta = processed_args.get('delta')
        
        if delta:
            result = deltaize_call(accessor_response.keys()[0], result)
        
        if s_unit == 'T':
            factor = 1e12
        elif s_unit == 'G':
            factor = 1e9
        elif s_unit == 'M':
            factor = 1e6
        elif s_unit == 'K':
            factor = 1e3
        else:
            factor = 1
        if 'm' in unit and s_unit:
            factor *= 1e3
        result = [round(x/factor, 3) for x in result]
        try:
            warn_lat = [is_within_range(warning, x) for x in result]
            crit_lat = [is_within_range(critical, x) for x in result]
        except:
            return {'returncode': 3, 'stdout': 'Bad Nagios range values'}
        if s_unit:
            unit = s_unit + unit.replace('m', '')
        if any(crit_lat):
            returncode = 2
            prefix = 'CRITICAL'
        elif any(warn_lat):
            returncode = 1
            prefix = 'WARNING'
        else:
            returncode = 0
            prefix = 'OK'
        label = accessor_response.keys()[0]
        name = label.capitalize()
        stdout = "%s: %s was " % (prefix, name)
        stdout = stdout.replace('|', '/')
        if delta:
            psec = '/sec'
        else:
            psec = ''
        stdout += ",".join([str(x) + unit + psec for x in result])
        perfdata = []
        count = 0
        for x in result:
            tmplabel = "%s_%d" % (label, count)
            count += 1
            pdata = "'%s'=%s%s" % (tmplabel, str(x),  unit)
            if warning:
                pdata += ';%s' % warning
            if critical:
                if not warning:
                    pdata += ';'
                pdata += ';%s' % critical
            perfdata.append(pdata)
        perfdata = ' '.join(perfdata)
        stdout = "%s|%s" % (stdout, perfdata)
        
    return {'returncode': returncode, 'stdout': stdout}


def is_within_range(nagios_range, value):
    """Returns False if the given value will raise an alert for the given
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


def get_plugin_instructions(plugin_name, config):
    """Returns the instruction to use for the given plugin.
    If nothing exists for the suffix, then simply return the basic

    $plugin_name $plugin_args

    """
    _, extension = os.path.splitext(plugin_name)
    try:
        return config.get('plugin directives', extension)
    except ConfigParser.NoOptionError:
        return '$plugin_name $plugin_args'


def execute_plugin(plugin_name, plugin_args, config):
    """Runs custom scripts that MUST be located in the scripts subdirectory
    of the executable
    
    """
    #Assemble our absolute plugin file name for calling
    plugin_path = config.get('plugin directives', 'plugin_path')
    plugin_abs_path = os.path.join(plugin_path, plugin_name)

    #Get any special instructions from the config for executing the plugin
    instructions = get_plugin_instructions(plugin_abs_path, config)

    #Make our command line
    cmd = get_cmdline(plugin_abs_path, plugin_args, instructions)
    
    logging.debug('Running process with command line: `%s`', ' '.join(cmd))
    
    running_check = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    running_check.wait()

    returncode = running_check.returncode
    stdout = ''.join(running_check.stdout.readlines()).replace('\r\n', '\n').replace('\r', '\n').strip()
    
    return {'returncode': returncode, 'stdout': stdout}

