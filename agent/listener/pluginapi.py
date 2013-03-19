import subprocess
import os
import ConfigParser
import logging
import shlex
import re
import string

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

def make_plugin_response_from_accessor(accessor_response, accessor_args):
    try:
        tmp = [x.split('=') for x in accessor_args.split('&')]
        processed_args = {}
        for k,v in tmp:
            processed_args[k] = v
    except ValueError, e:
        logging.debug('No argument detected in string %s' % accessor_args)
        processed_args = {}
    except Exception, e:
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
            factor = factor * 1e3
        result = [round(x/factor, 3) for x in result]
        warn_lat = [is_within_range(warning, x) for x in result]
        crit_lat = [is_within_range(critical, x) for x in result]
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
        stdout += ",".join([str(x) + unit for x in result])
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
    
def is_within_range(trange, value):
        '''
        Given a string Nagios range code, and a return value from
        a plugin, returns true if value is withing the range value
        '''
        #~ If its blank, return False so that it will never trigger an alert
        if not trange:
            return False
        #~ If its only a number
        is_match = re.match(r'^(\d+)$', trange)
        if is_match:
            tvalue = float(is_match.group(1))
            return 0 >= value or value >= tvalue
        #~ If it contains a colon
        is_match = re.match(r'^(@?)(\d+|~):(\d*)$', trange)
        if is_match:
            at = is_match.group(1)
            try:
                bottom = float(is_match.group(2))
            except:
                bottom = float('-Inf')
            try:
                top = float(is_match.group(3))
            except:
                top = float('Inf')
            preliminary = value < bottom or value > top
            if at:
                return not preliminary
            else:
                return preliminary

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
    
    return {'returncode' : returncode, 'stdout' : stdout}
    
