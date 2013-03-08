import subprocess
import os
import ConfigParser
import logging
import shlex
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
    
