import logging
import ConfigParser
import BaseHTTPServer

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

class PosixDaemon(abstract.NCPADaemon):
    
    def __init__(self, *args, **kwargs):
        super(PosixDaemon, self).__init__(*args, **kwargs)
    
    def check_pid(self, pidfile, *args, **kwargs):
        '''
        Make sure there is no pid file that is designated for
        this process.
        '''
        try:
            f = open(pidfile)
            f.close()
            print '%s still exists, ncpa process must still be running.' % pidfile
            self.logger.warning('User attempted to restart, %s still exists, exiting.' % pidfile)
            sys.exit(1)
        except IOError:
            return False
    
    def write_pid(self, pidfile, pid, *args, **kwargs):
        '''
        Write the PID to the ncpa.pid file
        '''
        f = open(pidfile, 'w')
        f.write(str(pid))
        f.close()
    
    def start(self, *args, **kwargs):
        '''
        Do the event that daemon is meant to do.
        '''
        raise Exception("Instantiation of abstract base class.")
    
    def stop(self, pidfile, *args, **kwargs):
        '''Kill spawned daemon gracefully
        '''
        try:
            f = open(pidfile, 'r')
        except IOError:
            print 'No pid file exists at %s. Cannot terminate.' % pidfile
            sys.exit(1)
        ncpa_pid = f.read()
        f.close()
        try:
            os.kill(int(ncpa_pid), signal.SIGTERM)
        except OSError:
            print 'No process with pid, deleting pid.'
        else:
            self.draw_spinner('Terminating')
        os.remove(pidfile)
    
    def reload(self, *args, **kwargs):
        '''
        Call start and stop
        '''
        self.stop()
        self.start()
    
    def draw_spinner(self, text, *args, **kwargs):
        print "%s...\\" % text,
        syms = ['\\', '|', '/', '-']
        bs = '\b'

        for _ in range(2):
            for sym in syms:
                sys.stdout.write("\b%s" % sym)
                sys.stdout.flush()
                time.sleep(.15)
        print ''
