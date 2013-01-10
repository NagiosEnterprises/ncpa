import os

def enumerate_plugins():
    builtins  = ['check_memory', 'check_swap', 'check_cpu']
    builtins += os.listdir('plugins')
    return builtins
