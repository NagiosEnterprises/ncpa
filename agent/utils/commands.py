import os
import logging

def enumerate_plugins():
    builtins  = ['check_memory', 'check_swap', 'check_cpu']
    builtins += os.listdir('plugins')
    logging.warning('Found %s' % str(buildins))
    return builtins
