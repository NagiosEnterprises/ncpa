import psutil
import subprocess

def check_cpu(item):
    item.values = psutil.cpu_percent(percpu=True)
    item.unit = '%'
    item.nice = 'CPU_Load'
    item.set_stdout('CPU Utilization is at')
    return item

def check_swap(item):
    item.unit = '%'
    item.nice = 'Swap_Usage'
    item.set_values(psutil.swap_memory().percent)
    item.set_stdout('Swap Usage is at')
    return item

def check_memory(item):
    item.unit = '%'
    item.nice = 'Memory_Usage'
    item.set_values(psutil.virtual_memory().percent)
    item.set_stdout('Physical Memory Usage is at')
    return item
    
def check_custom(item, name, script_args, *args, **kwargs):
    '''
    Runs custom scripts that MUST be located in the scripts subdirectory
    of the executable
    
    Notice, this command will replace all semicolons
    '''
    import os
    import shlex
    
    command  = [os.path.abspath('scripts/%s' % (name))]
    command += shlex.split(script_args)
    
    if item.warning:
        command += ['-w', item.warning]
    if item.critical:
        command += ['-c', item.critical]
    
    running_check = subprocess.Popen(command)
    running_check.wait()
    
    item.returncode = running_check.returncode
    item.stdout = running_check.stdout.read()
