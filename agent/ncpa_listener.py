#!/usr/bin/env python

import optparse
import os
import logging
import ConfigParser
import BaseHTTPServer

def daemonize():
    '''
    Detach from the terminal and continue as a daemon
    '''
    # swiped from twisted/scripts/twistd.py
    # See http://www.erlenstar.demon.co.uk/unix/faq_toc.html#TOC16
    if os.fork():   # launch child and...
        os._exit(0) # kill off parent
    os.setsid()
    if os.fork():   # launch child and...
        os._exit(0) # kill off parent again.
    os.umask(077)
    null=os.open('/dev/null', os.O_RDWR)
    for i in range(3):
        try:
            os.dup2(null, i)
        except OSError, e:
            if e.errno != errno.EBADF:
                raise
    os.close(null)

class PConfigParser(ConfigParser.ConfigParser):
    
    def __init__(self, *args, **kwargs):
        ConfigParser.ConfigParser.__init__(self, *args, **kwargs)
    
    def read(self, file_path, *args, **kwargs):
        self.file_path = file_path
        ConfigParser.ConfigParser.read(self, file_path, *args, **kwargs)

class ConfigHTTPServer(BaseHTTPServer.HTTPServer):
    
    def __init__(self, config, *args, **kwargs):
        BaseHTTPServer.HTTPServer.__init__(self, *args, **kwargs)
        self.config = config

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
        self.config = PConfigParser()
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


def parse_args():
    
    usage = '%prog [start|stop|reload]'
    
    parser = optparse.OptionParser()
    
    parser.add_option('-c', '--config', help='Config file to use.', default='etc/ncpa.cfg')
    
    options, args = parser.parse_args()
    
    if not len(args) == 1 or args[0] not in ['start', 'stop', 'reload', 'debug']:
        parser.error('Must only give either start, stop or reload.')
    
    return options, args

if __name__ == "__main__":
    
    options, args = parse_args()
    
    if not platform.system() == 'Windows':
        daemon = daemons.posix.ListenerDaemon(config_filename=options.config)
        gen_daemon = getattr(daemon, args[0])
        gen_daemon()
    else:
        this_path = os.getcwd()
        daemon = daemons.windows.ListenerService
        daemons.windows.instart(daemon)
