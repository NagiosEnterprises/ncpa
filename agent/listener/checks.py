import psutil
import subprocess
import logging
import ConfigParser

def check_cpu(item, *args, **kwargs):
    item.values = psutil.cpu_percent(percpu=True)
    item.unit = '%'
    item.nice = 'CPU_Load'
    item.set_stdout('CPU Utilization is at')
    return item

def check_swap(item, *args, **kwargs):
    item.unit = '%'
    item.nice = 'Swap_Usage'
    item.set_values(psutil.swap_memory().percent)
    item.set_stdout('Swap Usage is at')
    return item

def check_memory(item, *args, **kwargs):
    item.unit = '%'
    item.nice = 'Memory_Usage'
    item.set_values(psutil.virtual_memory().percent)
    item.set_stdout('Physical Memory Usage is at')
    return item
    
def check_custom(item, plugin_name, plugin_args, config, *args, **kwargs):
    """
    Runs custom scripts that MUST be located in the scripts subdirectory
    of the executable
    
    Notice, this command will replace all semicolons and special shell
    characters that are found in the plugin_name or script_args, if you
    need to use those, then you need to define them in the agent.cfg
    file.
    """
    import os
    
    _, extension = os.path.splitext(plugin_name)
    plugin_name  = 'scripts/%s' % (plugin_name)
    cmd = []
    try:
        instruction = config.get('plugin suffix instructions', extension)
        logging.debug('Executing the plugin with instruction contained in config. Instruction is: %s', instruction)
        cmd += get_cmdline_instruct(item, plugin_name, plugin_args, instruction)
    except ConfigParser.NoOptionError:
        logging.debug('Executing the plugin with instruction by execution.')
        cmd += get_cmdline_no_instruct(item, plugin_name, plugin_args)
    
    logging.debug('Running process with command line: %s',' '.join(cmd))
    
    running_check = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    running_check.wait()
    
    item.returncode = running_check.returncode
    item.stdout = running_check.stdout.read()
    
    return item

def get_cmdline_instruct(item, plugin_name, plugin_args, instruction):
    """
    Execute with special instructions.
    
    TODO - Investigate better parameter passing
    
    EXAMPLE instruction (Powershell):
    powershell -ExecutionPolicy Unrestricted $plugin_name $plugin_args
    
    EXAMPLE instruction (VBS):
    wscript $plugin_name $plugin_args
    """
    import shlex
    import string
    template = string.Template(instruction)
    named    = template.substitute(plugin_name=plugin_name, plugin_args=plugin_args)
    
    command = []
    for x in shlex.split(named):
        safe = x.replace('\0', '')
        if safe:
            command.append(safe)
    
    return command

def get_cmdline_no_instruct(item, plugin_name, plugin_args):
    """
    Execute the script normally, with no special considerations.
    """
    import shlex
    
    command  = [plugin_name]
    command += shlex.split(plugin_args)
    
    if item.warning:
        command += ['-w', item.warning]
    if item.critical:
        command += ['-c', item.critical]
    
    return command
