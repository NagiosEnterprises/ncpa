import subprocess
import os
import ConfigParser
import logging
import shlex
import re
import string
import urlparse
import tempfile
import pickle
import time


def try_both(plugin_name, plugin_args, config):
    """Try both the builtin and named plugin, in that order.
    """
    try:
        execute_plugin(plugin_name, plugin_args, config)
    except:
        execute_named(plugin_name, plugin_args)


def get_cmdline_instruct(plugin_name, plugin_args, instruction):
    """
    Execute with special instructions.
    
    TODO - Investigate better parameter passing
    
    EXAMPLE instruction (Powershell):
    powershell -ExecutionPolicy Unrestricted $plugin_name $plugin_args
    
    EXAMPLE instruction (VBS):
    wscript $plugin_name $plugin_args
    """
    template = string.Template(instruction)
    named    = template.substitute(plugin_name=plugin_name, plugin_args=plugin_args)
    
    command = []
    for x in shlex.split(named):
        safe = x.replace('\0', '')
        if safe:
            command.append(safe)
    
    return command


def get_cmdline_no_instruct(plugin_name, plugin_args):
    """
    Execute the script normally, with no special considerations.
    """
    return [plugin_name] + shlex.split(plugin_args)


def deltaize_call(keyname, result):
    filename = "ncpa-%s.tmp" % str(hash(keyname))
    tmpfile = os.path.join(tempfile.gettempdir(), filename)
    oresult = result[:]
    modified = 0
    
    try:
        fresult = open(tmpfile, 'r')
        modified = os.path.getmtime(tmpfile)
        oresult = pickle.load(fresult)
        fresult.close()
    except:
        logging.warning('Error opening tmpfile: ', tmpfile)
        fresult = open(tmpfile, 'w')
        pickle.dump(result, fresult)
        fresult.close()
        return [0 for x in result]
    
    delta = time.time() - modified
    return [abs((x - y) / delta) for x,y in zip(oresult, result)]


def make_plugin_response_from_accessor(accessor_response, accessor_args):
    try:
        processed_args = dict(urlparse.parse_qsl(accessor_args))
    except ValueError, e:
        logging.debug('No argument detected in string %s' % accessor_args)
        processed_args = {}
    except Exception, e:
        processed_args = {}
        logging.exception(e)
        logging.warning('Unabled to process arguments.')
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
        if not type(result) in [list, tuple]:
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
        
    return {'returncode':returncode, 'stdout':stdout}
    
def is_within_range(nagstring, value):
    if not nagstring:
        return False
    import re
    import operator
    first_float = r'(?P<first>(-?[0-9]+(\.[0-9]+)?))'
    second_float= r'(?P<second>(-?[0-9]+(\.[0-9]+)?))'
    actions = [(r'^%s$' % first_float, lambda y: (value > float(y.group('first'))) or (value < 0)),
               (r'^%s:$' % first_float, lambda y: value < float(y.group('first'))),
               (r'^~:%s$' % first_float, lambda y: value > float(y.group('first'))),
               (r'^%s:%s$' % (first_float, second_float), lambda y: (value < float(y.group('first'))) or (value > float(y.group('second')))),
               (r'^@%s:%s$' % (first_float, second_float), lambda y: not((value < float(y.group('first'))) or (value > float(y.group('second')))))]
    for regstr, func in actions:
        res = re.match(regstr,nagstring)
        if res: 
            return func(res)
    raise Exception('Improper warning/critical format.')


def execute_plugin(plugin_name, plugin_args, config, *args, **kwargs):
    """
    Runs custom scripts that MUST be located in the scripts subdirectory
    of the executable
    
    Notice, this command will replace all semicolons and special shell
    characters that are found in the plugin_name or script_args, if you
    need to use those, then you need to define them in the agent.cfg
    file.
    """
    
    _, extension = os.path.splitext(plugin_name)
    plugin_name = os.path.join(config.get('plugin directives', 'plugin_path'), plugin_name)
    plugin_name = '"%s"' % plugin_name
    cmd = []
    try:
        instruction = config.get('plugin directives', extension)
        logging.debug('Executing the plugin with instruction contained in config. Instruction is: %s', instruction)
        cmd += get_cmdline_instruct(plugin_name, plugin_args, instruction)
    except ConfigParser.NoOptionError:
        logging.debug('Executing the plugin with instruction by execution.')
        cmd += get_cmdline_no_instruct(plugin_name, plugin_args)
    
    logging.debug('Running process with command line: %s', str(cmd))
    
    running_check = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    running_check.wait()
    
    returncode = running_check.returncode
    stdout = ''.join(running_check.stdout.readlines()).replace('\r\n', '\n').replace('\r', '\n')
    
    return {'returncode': returncode, 'stdout': stdout}

