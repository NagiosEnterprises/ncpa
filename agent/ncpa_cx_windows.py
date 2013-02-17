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

class Handler(object):

    # no parameters are permitted; all configuration should be placed in the
    # configuration file and handled in the Initialize() method
    def __init__(self):
        cx_Logging.Info("creating handler instance")
        self.stopEvent = cx_Threads.Event()
    
    def determine_relative_filename(self, file_name, *args, **kwargs):
        '''Gets the relative pathname of the executable being run.
        
        This is meant exclusively for being used with cx_Freeze on Windows.
        '''
        import sys
        appdir = os.path.dirname(sys.path[0])
        return os.path.join(appdir, file_name)
    
    def parse_config(self, *args, **kwargs):
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.config_filename)
    
    def setup_logging(self, *arg, **kwargs):
        '''This should always setup the logger.
        '''
        log_config = dict(self.config.items('logging', 1))
        log_config['level'] = getattr(logging, log_config['log_level'], logging.INFO)
        del log_config['log_level']
        log_file = log_config['filename']
        if os.path.isabs(log_file):
            log_config['filename'] = log_file
        else:
            log_config['filename'] = self.determine_relative_filename(log_file)
        logging.basicConfig(**log_config)
        self.logger = logging.getLogger()
    
    def start(self):
        '''Kickoff the TCP Server
        
        @todo Integrate this with the Windows code. It shares so much...and gains so little
        ''' 
        try:
            import listener.server
            address = self.config.get('listening server', 'ip')
            port = int(self.config.get('listening server', 'port'))
            listener.server.listener.config['iconfig'] = self.config
            listener.server.listener.run(address, port)
            # url_for('static', filename='chinook.css')
            # url_for('static', filename='jquery-1.8.3.min.js')
            # url_for('static', filename='jquery-ui.css')
            # url_for('static', filename='jquery-ui.js')
        except Exception, e:
            self.logger.exception(e)
        
    # called when the service is starting
    def Initialize(self, configFileName):
        self.config_filename = self.determine_relative_filename('etc/ncpa.cfg')
        self.parse_config()
        self.setup_logging()
        self.logger.info(self.config_filename)

    # called when the service is starting immediately after Initialize()
    # use this to perform the work of the service; don't forget to set or check
    # for the stop event or the service GUI will not respond to requests to
    # stop the service
    def Run(self):
        cx_Logging.Info("running service....")
        self.start()
        self.stopEvent.Wait()

    # called when the service is being stopped by the service manager GUI
    def Stop(self):
        cx_Logging.Info("stopping service...")
        self.stopEvent.Set()
