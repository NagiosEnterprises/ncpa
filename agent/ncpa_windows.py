"""
Implements a simple service using cx_Freeze.

See below for more information on what methods must be implemented and how they
are called.
"""

#import cx_Logging
#import cx_Threads
import threading
import ConfigParser
import glob
import logging
import logging.handlers
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
import ssl
from gevent import monkey
import ssl_patch

monkey.patch_all(subprocess=True)


class Base(object):
    # no parameters are permitted; all configuration should be placed in the
    # configuration file and handled in the Initialize() method
    def __init__(self, debug=False):
        logging.getLogger().handlers = []
        self.stopEvent = threading.Event()
        self.debug = debug

    def determine_relative_filename(self, file_name, *args, **kwargs):
        """Gets the relative pathname of the executable being run.

        This is meant exclusively for being used with cx_Freeze on Windows.
        """
        if self.debug:
            appdir = os.path.dirname(filename.__file__)
        else:
            appdir = os.path.dirname(sys.path[0])

        # There is something wonky about Windows and its need for paths and how Python
        # pulls the above appdir, which doesn't come out absolute when the application
        # is frozen. Figured being absolutely sure its an absolute path here.
        return os.path.abspath(os.path.join(appdir, file_name))

    def parse_config(self, *args, **kwargs):
        self.config = ConfigParser.ConfigParser()
        self.config.optionxform = str
        self.config.read(self.config_filenames)

    def setup_plugins(self):
        plugin_path = self.config.get('plugin directives', 'plugin_path')
        abs_plugin_path = self.determine_relative_filename(plugin_path)
        self.abs_plugin_path = os.path.normpath(abs_plugin_path)
        self.config.set('plugin directives', 'plugin_path', self.abs_plugin_path)

    def setup_logging(self, *args, **kwargs):
        """This should always setup the logger.

        """
        config = dict(self.config.items(self.c_type, 1))

        # Now we grab the logging specific items
        log_level_str = config.get('loglevel', 'INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)

        log_file = os.path.normpath(config['logfile'])
        if not os.path.isabs(log_file):
            log_file = self.determine_relative_filename(log_file)

        logging.getLogger().handlers = []

        # Max size of log files will be 20MB, and we'll keep one of them as backup
        max_log_size_bytes = int(config.get('logmaxmb', 5))
        max_log_rollovers = int(config.get('logbackups', 5))
        max_file_size = max_log_size_bytes * 1024 * 1024
        file_handler = logging.handlers.RotatingFileHandler(log_file,
                                                            maxBytes=max_file_size,
                                                            backupCount=max_log_rollovers)
        file_format = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(message)s')
        file_handler.setFormatter(file_format)

        logging.getLogger().addHandler(file_handler)
        logging.getLogger().setLevel(log_level)

    # called when the service is starting immediately after Initialize()
    # use this to perform the work of the service; don't forget to set or check
    # for the stop event or the service GUI will not respond to requests to
    # stop the service
    def Run(self):
        self.start()
        self.stopEvent.Wait()

    # called when the service is being stopped by the service manager GUI
    def Stop(self):
        pass
        self.stopEvent.Set()


class Listener(Base):

    def start(self):
        """Kickoff the TCP Server

        """
        try:
            address = self.config.get('listener', 'ip')
            port = self.config.getint('listener', 'port')
            listener.server.listener.config_files = self.config_filenames
            listener.server.listener.tail_method = listener.windowslogs.tail_method
            listener.server.listener.config['iconfig'] = self.config

            try:
                ssl_version = getattr(ssl, 'PROTOCOL_' + ssl_str_version)
            except:
                ssl_version = getattr(ssl, 'PROTOCOL_TLSv1')
                ssl_str_version = 'TLSv1'
            logging.info('Using SSL version %s', ssl_str_version)

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
        self.config_filenames = [self.determine_relative_filename(
	    os.path.join('etc', 'ncpa.cfg'))]
	self.config_filenames.extend(sorted(glob.glob(
	    self.determine_relative_filename(os.path.join(
	        'etc', 'ncpa.cfg.d', '*.cfg')))))
        self.parse_config()
        self.setup_logging()
        self.setup_plugins()
        logging.info("Parsed config from: %s" % str(self.config_filenames))
        logging.info("Looking for plugins at: %s" % self.abs_plugin_path)


class Passive(Base):

    def run_all_handlers(self, *args, **kwargs):
        """Will run all handlers that exist.

        The handler must:
        - Have a config header entry
        - Abide by the handler API set forth by passive.abstract.NagiosHandler
        - Terminate in a timely fashion
        """
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
        self.config_filenames = [self.determine_relative_filename(
	    os.path.join('etc', 'ncpa.cfg'))]
	self.config_filenames.extend(sorted(glob.glob(
	    self.determine_relative_filename(os.path.join(
	        'etc', 'ncpa.cfg.d', '*.cfg')))))
        self.parse_config()
        self.setup_logging()
        self.setup_plugins()
        logging.info("Parsed config from: %s" % str(self.config_filenames))
        logging.info("Looking for plugins at: %s" % self.config.get('plugin directives', 'plugin_path'))
