import logging
import ConfigParser

class NCPADaemon(object):
    '''
    Defines the general form that listener daemons must adhere
    to. Override all of these methods.
    '''
    
    def __init__(self, config_filename, *args, **kwargs):
        '''
        Always inherit this method
        '''
        self.config_filename = config_filename
        self.parse_config()
        self.setup_logging()
    
    def parse_config(self, *args, **kwargs):
        '''
        Set the parsed config to self.config
        '''
        self.config = ConfigParser.ConfigParser()
        self.config.optionxform = str
        self.config.read(self.config_filename)
    
    def setup_logging(self, *arg, **kwargs):
        '''
        This should always setup the logger.
        '''
        log_config = dict(self.config.items('logging', 1))
        log_config['level'] = getattr(logging, log_config['log_level'], logging.INFO)
        del log_config['log_level']
        logging.basicConfig(**log_config)
        self.logger = logging.getLogger()
    
    def start(self, *args, **kwargs):
        '''
        This method should start the daemon or persistent
        process.
        '''
        raise Exception("Instantiation of abstract base class.")
    
    def stop(self, *args, **kwargs):
        '''
        This should kill the daemon and shut down everything
        tidily.
        '''
        raise Exception("Instantiation of abstract base class.")
