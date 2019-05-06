#!/usr/bin/env python

import warnings
warnings.simplefilter('ignore')

import ncpadaemon
import logging
import time
import datetime
import sys
import os
import filename
import passive.nrds
import passive.nrdp
import passive.kafkaproducer


class Passive(ncpadaemon.Daemon):

    default_conf = os.path.abspath(os.path.join(filename.get_dirname_file(), 'etc', 'ncpa.cfg'))
    section = u'passive'

    def run_all_handlers(self, *args, **kwargs):
        """
        Will run all handlers that exist.

        The handler must:
        - Have a config header entry
        - Abide by the handler API set forth by passive.abstract.NagiosHandler
        - Terminate in a timely fashion
        """
        handlers = self.config_parser.get('passive', 'handlers').split(',')
        run_time = time.time()

        # Empty passive handlers will skip trying to run any handlers
        if handlers[0] == 'None' or handlers[0] == '':
            return

        for handler in handlers:
            try:
                handler = handler.strip()
                module_name = 'passive.%s' % handler
                __import__(module_name)
                tmp_handler = sys.modules[module_name]
            except ImportError as e:
                logging.error('Could not import module passive.%s, skipping. %s' % (handler, str(e)))
                logging.exception(e)
            else:
                try:
                    ins_handler = tmp_handler.Handler(self.config_parser)
                    ins_handler.run(run_time)
                    logging.debug(u'Successfully ran handler %s' % handler)
                except Exception as e:
                    logging.exception(e)

    def run(self):

        # Read config once (restart required for new configs)
        self.read_basic_config()
        plugins_abs = os.path.abspath(os.path.join(filename.get_dirname_file(), self.config_parser.get(u'plugin directives', u'plugin_path')))
        self.config_parser.set(u'plugin directives', u'plugin_path', plugins_abs)
        self.config_parser.file_path = self.default_conf

        # Check if there is a start delay
        try:
            delay_start = self.config_parser.get('passive', 'delay_start')
            if delay_start:
                logging.info('Delayed start in configuration. Waiting %s seconds to start.', delay_start)
                time.sleep(int(delay_start))
        except Exception:
            pass

        # Set next DB maintenance period to +1 day
        self.db.run_db_maintenance(self.config_parser)
        next_db_maintenance = datetime.datetime.now() + datetime.timedelta(days=1)

        try:
            while True:
                self.run_all_handlers()

                # Do DB maintenance if the time is greater than next DB maintenance run
                if datetime.datetime.now() > next_db_maintenance:
                    self.db.run_db_maintenance(self.config_parser)
                    next_db_maintenance = datetime.datetime.now() + datetime.timedelta(days=1)

                time.sleep(1)
        except Exception, e:
            logging.exception(e)


if __name__ == u'__main__':
    try:
        Passive().main()
    except Exception, e:
        logging.exception(e)
