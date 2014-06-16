import ncpadaemon
import logging
import time
import sys
import os
import filename
import passive.nrds
import passive.nrdp

class Passive(ncpadaemon.Daemon):
    default_conf = os.path.abspath(os.path.join(filename.get_dirname_file(), 'etc', 'ncpa.cfg'))
    section = u'passive'

    def run_all_handlers(self, *args, **kwargs):
        u"""Will run all handlers that exist.

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
                logging.error(u'Could not import module passive.%s, skipping...' % handler)
            else:
                try:
                    plugins_abs = os.path.abspath(self.config_parser.get(u'plugin directives', u'plugin_path'))
                    self.config_parser.set(u'plugin directives', u'plugin_path', plugins_abs)
                    self.config_parser.file_path = os.path.abspath(u'etc/ncpa.cfg')
                    ins_handler = tmp_handler.Handler(self.config_parser)
                    ins_handler.run()
                    logging.debug(u'Successfully ran handler %s' % handler)
                except Exception, e:
                    logging.exception(e)

    def run(self):
        while True:
            self.read_basic_config()
            try:
                self.run_all_handlers()
            except Exception, e:
                logging.exception(e)
            sleep = int(self.config_parser.get(u'passive', u'sleep'))
            time.sleep(sleep)

if __name__ == u'__main__':
    try:
        Passive().main()
    except Exception, e:
        logging.exception(e)
