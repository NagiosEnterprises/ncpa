import os
import json
import logging

def enumerate_plugins(*args, **kwargs):
    try:
        builtins  = ['check_memory', 'check_swap', 'check_cpu']
        builtins += [x for x in os.listdir('plugins') if os.path.isfile('plugins/%s' % x)]
        count = len(builtins)
        return json.dumps({    'plugins' : builtins,
                                'count' : count })
    except Exception, e:
        logging.exception(e)
        return json.dumps({'error' : str(e)})
        
