#!/usr/bin/env python

import ncpadaemon
import logging
import time
import sys
import os

import passive.nrds
import passive.nrdp


class Passive(ncpadaemon.Daemon):
    default_conf = os.path.abspath('etc/ncpa.cfg')
    section = 'passive'
    
    def run_all_handlers(self, *args, **kwargs):
        """Will run all handlers that exist.

        The handler must:
        - Have a config header entry
        - Abide by the handler API set forth by passive.abstract.NagiosHandler
        - Terminate in a timely fashion
        """
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
                    plugins_abs = os.path.abspath(self.config_parser.get('plugin directives', 'plugin_path'))
                    self.config_parser.set('plugin directives', 'plugin_path', plugins_abs)
                    self.config_parser.file_path = os.path.abspath('etc/ncpa.cfg')
                    ins_handler = tmp_handler.Handler(self.config_parser)
                    ins_handler.run()
                    logging.debug('Successfully ran handler %s' % handler)
                except Exception as e:
                    logging.exception(e)
    
    def run(self):
        while True:
            self.read_basic_config()
            try:
                self.run_all_handlers()
            except Exception as e:
                logging.exception(e)
            sleep = int(self.config_parser.get('passive', 'sleep'))
            time.sleep(sleep)

if __name__ == '__main__':
    try:
        Passive().main()
    except Exception as e:
        logging.exception(e)
