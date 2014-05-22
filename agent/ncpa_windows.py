u"""
Implements a simple service using cx_Freeze.

See below for more information on what methods must be implemented and how they
are called.
"""

import cx_Logging
import cx_Threads
import ConfigParser
import logging
import os
import time
import sys

# DO NOT REMOVE THIS, THIS FORCES cx_Freeze to include the library
# DO NOT REMOVE ANYTHING BELOW THIS LINE
import passive.nrds
import passive.nrdp
import listener.server
import listener.certificate
import jinja2.ext
import filename

DEBUG = 0


class Base(object):
    # no parameters are permitted; all configuration should be placed in the
    # configuration file and handled in the Initialize() method
    def __init__(self):
        cx_Logging.Info(u"creating handler instance")
        self.stopEvent = cx_Threads.Event()

    def determine_relative_filename(self, file_name, *args, **kwargs):
        u'''Gets the relative pathname of the executable being run.

        This is meant exclusively for being used with cx_Freeze on Windows.
        '''
        global DEBUG
        if DEBUG == 0:
            appdir = os.path.dirname(sys.path[0])
        elif DEBUG == 1:
            appdir = os.path.dirname(filename.__file__)
        return os.path.join(appdir, file_name)

    def parse_config(self, *args, **kwargs):
        self.config = ConfigParser.ConfigParser()
        self.config.optionxform = unicode
        self.config.read(self.config_filename)

    def setup_plugins(self):
        plugin_path = self.config.get(u'plugin directives', u'plugin_path')
        self.abs_plugin_path = self.determine_relative_filename(plugin_path)
        self.config.set(u'plugin directives', u'plugin_path', self.abs_plugin_path)

    def setup_logging(self, *arg, **kwargs):
        u'''This should always setup the logger.
        '''
        log_config = dict(self.config.items(self.c_type, 1))
        log_level = log_config.get(u'loglevel', u'INFO').upper()
        log_config[u'level'] = getattr(logging, log_level, logging.INFO)
        del log_config[u'loglevel']
        log_file = log_config[u'logfile']
        if os.path.isabs(log_file):
            log_config[u'filename'] = log_file
        else:
            log_config[u'filename'] = self.determine_relative_filename(log_file)
        logging.basicConfig(**log_config)
        self.logger = logging.getLogger()

    # called when the service is starting immediately after Initialize()
    # use this to perform the work of the service; don't forget to set or check
    # for the stop event or the service GUI will not respond to requests to
    # stop the service
    def Run(self):
        cx_Logging.Info(u"running service....")
        self.start()
        self.stopEvent.Wait()

    # called when the service is being stopped by the service manager GUI
    def Stop(self):
        cx_Logging.Info(u"stopping service...")
        self.stopEvent.Set()


class Listener(Base):

    def start(self):
        u'''Kickoff the TCP Server

        TODO: Integrate this with the Windows code. It shares so much...and gains so little
        ''' 
        try:
            address = self.config.get(u'listener', u'ip')
            port = int(self.config.get(u'listener', u'port'))
            listener.server.listener.config_file = self.config_filename
            listener.server.listener.config[u'iconfig'] = self.config

            user_cert = self.config_parser.get('listener', 'certificate')

            if user_cert == 'adhoc':
                basepath = self.determine_relative_filename('')
                cert, key = listener.certificate.create_self_signed_cert(basepath, 'ncpa.crt', 'ncpa.key')
            else:
                cert, key = user_cert.split(',')
            ssl_context = {'certfile': cert, 'keyfile': key}

            listener.server.listener.secret_key = os.urandom(24)
            http_server = HTTPServer(WSGIContainer(listener.server.listener),
                                     ssl_options=ssl_context)
            http_server.listen(port)
            IOLoop.instance().start()
        except Exception, e:
            self.logger.exception(e)

    # called when the service is starting
    def Initialize(self, config_file):
        self.c_type = u'listener'
        self.config_filename = self.determine_relative_filename(os.path.join(u'etc', u'ncpa.cfg'))
        self.parse_config()
        self.setup_logging()
        self.setup_plugins()
        self.logger.info(u"Looking for config at: %s" % self.config_filename)
        self.logger.info(u"Looking for plugins at: %s" % self.abs_plugin_path)


class Passive(Base):

    def run_all_handlers(self, *args, **kwargs):
        u'''Will run all handlers that exist.

        The handler must:
        - Have a config header entry
        - Abide by the handler API set forth by passive.abstract.NagiosHandler
        - Terminate in a timely fashion
        '''
        handlers = self.config.get(u'passive', u'handlers').split(u',')

        for handler in handlers:
            try:
                module_name = 'passive.%s' % handler
                __import__(module_name)
                tmp_handler = sys.modules[module_name]
            except ImportError, e:
                self.logger.error(u'Could not import module passive.%s, skipping. %s' % (handler, unicode(e)))
                self.logger.exception(e)
            else:
                try:
                    ins_handler = tmp_handler.Handler(self.config)
                    ins_handler.run()
                    self.logger.debug(u'Successfully ran handler %s' % handler)
                except Exception, e:
                    self.logger.exception(e)

    def start(self):
        try:
            while True:
                self.run_all_handlers()
                self.parse_config()
                wait_time = int(self.config.get(u'passive', u'sleep'))
                time.sleep(wait_time)
        except Exception, e:
            self.logger.exception(e)

    # called when the service is starting
    def Initialize(self, config_file):
        self.c_type = u'passive'
        self.config_filename = self.determine_relative_filename(os.path.join(u'etc', u'ncpa.cfg'))
        self.parse_config()
        self.setup_logging()
        self.setup_plugins()
        self.logger.info(u"Looking for config at: %s" % self.config_filename)
        self.logger.info(u"Looking for plugins at: %s" % self.config.get(u'plugin directives', u'plugin_path'))

if DEBUG == 1:
    if len(sys.argv) == 3 and sys.argv[1] == u'debug':
        if sys.argv[2] == u'passive':
            a = Passive()
        elif sys.argv[2] == u'listener':
            a = Listener()
        a.Initialize((u'agent', u'etc', u'ncpa.cfg'))
        a.Run()
