#!/usr/bin/env python

import simpledaemon
import logging
import time
import sys

class Passive(simpledaemon.Daemon):
    default_conf = 'etc/ncpa.cfg'
    section = 'passive'
    
    def run_all_handlers(self, *args, **kwargs):
        '''Will run all handlers that exist.
        
        The handler must:
        - Have a config header entry
        - Abide by the handler API set forth by passive.abstract.NagiosHandler
        - Terminate in a timely fashion
        '''
        handlers = self.config_parser.get('passive', 'handlers').split(',')
        
        for handler in handlers:
            try:
                handler = handler.strip()
                module_name = 'passive.%s' % handler
                __import__(module_name)
                tmp_handler = sys.modules[module_name]
            except ImportError:
                logging.error('Could not import module passive.%s, skipping...' % handler)
            else:
                try:
                    ins_handler = tmp_handler.Handler(self.config_parser)
                    ins_handler.run()
                    logging.debug('Successfully ran handler %s' % handler)
                except Exception, e:
                    logging.exception(e)
    
    def run(self):
        while True:
            self.read_basic_config()
            try:
                self.run_all_handlers()
            except Exception, e:
                logging.exception(e)
            sleep = int(self.config_parser.get('passive', 'sleep'))
            time.sleep(sleep)

if __name__ == '__main__':
    Passive().main()
