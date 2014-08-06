"""
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
from gevent.pywsgi import WSGIServer
from gevent.pool import Pool
# DO NOT REMOVE THIS, THIS FORCES cx_Freeze to include the library
# DO NOT REMOVE ANYTHING BELOW THIS LINE
import passive.nrds
import passive.nrdp
import listener.server
import listener.psapi
import listener.windowscounters
import listener.windowslogs
import listener.certificate
import jinja2.ext
import webhandler
import filename
from gevent import monkey

monkey.patch_all()


class Base(object):
    # no parameters are permitted; all configuration should be placed in the
    # configuration file and handled in the Initialize() method
    def __init__(self, debug=False):
        cx_Logging.Info("Creating handler instance...")
        self.stopEvent = cx_Threads.Event()
        self.debug = debug

    def determine_relative_filename(self, file_name, *args, **kwargs):
        '''Gets the relative pathname of the executable being run.

        This is meant exclusively for being used with cx_Freeze on Windows.
        '''
        if self.debug:
            appdir = os.path.dirname(filename.__file__)
        else:
            appdir = os.path.dirname(sys.path[0])
        return os.path.join(appdir, file_name)

    def parse_config(self, *args, **kwargs):
        self.config = ConfigParser.ConfigParser()
        self.config.optionxform = str
        self.config.read(self.config_filename)

    def setup_plugins(self):
        plugin_path = self.config.get('plugin directives', 'plugin_path')
        abs_plugin_path = self.determine_relative_filename(plugin_path)
        self.abs_plugin_path = os.path.normpath(abs_plugin_path)
        self.config.set('plugin directives', 'plugin_path', self.abs_plugin_path)

    def setup_logging(self, *arg, **kwargs):
        '''This should always setup the logger.
        '''
        log_config = dict(self.config.items(self.c_type, 1))
        log_level = log_config.get('loglevel', 'INFO').upper()
        log_config['level'] = getattr(logging, log_level, logging.INFO)
        del log_config['loglevel']
        log_file = log_config['logfile']
        if os.path.isabs(log_file):
            log_config['filename'] = log_file
        else:
            log_config['filename'] = self.determine_relative_filename(log_file)
        logging.basicConfig(**log_config)

    # called when the service is starting immediately after Initialize()
    # use this to perform the work of the service; don't forget to set or check
    # for the stop event or the service GUI will not respond to requests to
    # stop the service
    def Run(self):
        cx_Logging.Info("Running service....")
        self.start()
        self.stopEvent.Wait()

    # called when the service is being stopped by the service manager GUI
    def Stop(self):
        cx_Logging.Info("Stopping service...")
        self.stopEvent.Set()


class Listener(Base):

    def start(self):
        '''Kickoff the TCP Server

        '''
        try:
            address = self.config.get('listener', 'ip')
            port = self.config.getint('listener', 'port')
            listener.server.listener.config_file = self.config_filename
            listener.server.listener.tail_method = listener.windowslogs.tail_method
            listener.server.listener.config['iconfig'] = self.config

            user_cert = self.config.get('listener', 'certificate')

            if user_cert == 'adhoc':
                basepath = self.determine_relative_filename('')
                cert, key = listener.certificate.create_self_signed_cert(basepath, 'ncpa.crt', 'ncpa.key')
            else:
                cert, key = user_cert.split(',')
            ssl_context = {'certfile': cert, 'keyfile': key}

            listener.server.listener.secret_key = os.urandom(24)
            http_server = WSGIServer(listener=(address, port),
                                     application=listener.server.listener,
                                     handler_class=webhandler.PatchedWSGIHandler,
                                     spawn=Pool(100),
                                     **ssl_context)
            http_server.serve_forever()
        except Exception, e:
            logging.exception(e)

    # called when the service is starting
    def Initialize(self, config_file):
        self.c_type = 'listener'
        self.config_filename = self.determine_relative_filename(os.path.join('etc', 'ncpa.cfg'))
        self.parse_config()
        self.setup_logging()
        self.setup_plugins()
        logging.info("Looking for config at: %s" % self.config_filename)
        logging.info("Looking for plugins at: %s" % self.abs_plugin_path)


class Passive(Base):

    def run_all_handlers(self, *args, **kwargs):
        '''Will run all handlers that exist.

        The handler must:
        - Have a config header entry
        - Abide by the handler API set forth by passive.abstract.NagiosHandler
        - Terminate in a timely fashion
        '''
        handlers = self.config.get('passive', 'handlers').split(',')

        for handler in handlers:
            try:
                module_name = 'passive.%s' % handler
                __import__(module_name)
                tmp_handler = sys.modules[module_name]
            except ImportError, e:
                logging.error('Could not import module passive.%s, skipping. %s' % (handler, str(e)))
                logging.exception(e)
            else:
                try:
                    ins_handler = tmp_handler.Handler(self.config)
                    ins_handler.run()
                    logging.debug('Successfully ran handler %s' % handler)
                except Exception, e:
                    logging.exception(e)

    def start(self):
        try:
            while True:
                self.run_all_handlers()
                self.parse_config()
                wait_time = self.config.getint('passive', 'sleep')
                time.sleep(wait_time)
        except Exception, e:
            logging.exception(e)

    # called when the service is starting
    def Initialize(self, config_file):
        self.c_type = 'passive'
        self.config_filename = self.determine_relative_filename(os.path.join('etc', 'ncpa.cfg'))
        self.parse_config()
        self.setup_logging()
        self.setup_plugins()
        logging.info("Looking for config at: %s" % self.config_filename)
        logging.info("Looking for plugins at: %s" % self.config.get('plugin directives', 'plugin_path'))
