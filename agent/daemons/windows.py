import pythoncom
import win32serviceutil
import win32service
import win32event
import servicemanager
import SocketServer
import threading
from os.path import splitext, abspath
from sys import modules
import logging
import ConfigParser
import win32serviceutil
import win32service
import win32event
import win32api
import inspect
import re
import sys
import time
import abstract

def import_basedir():
    agent = re.compile(r'(.*agent.?)')
    this_module = inspect.currentframe().f_code.co_filename
    res = agent.search(this_module).group(1)
    sys.path.append(res)

class ListenerService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'NCPAListener'
    _svc_display_name_ = 'NCPA Listener'
    _svc_description = 'Service that listens on a TCP port.'
    
    def __init__(self, *args):
        win32serviceutil.ServiceFramework.__init__(self, *args)
        self.log('init')
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.config_filename = self.determine_filename('etc/ncpa.cfg')
        self.parse_config()
        self.setup_logging()
    
    def determine_filename(self, suffix, *args, **kwargs):
        agent = re.compile(r'(.*agent.?)')
        this_module = inspect.currentframe().f_code.co_filename
        res = agent.search(this_module).group(1)
        return res + suffix
    
    def import_handler(self):
        '''Imports the handlers in the Windows fashion.
        
        @todo Change it so the way the import is handled is sane. This works, but it needs to be reworked.
        '''
        agent = re.compile(r'(.*agent.?)')
        this_module = inspect.currentframe().f_code.co_filename
        res = agent.search(this_module).group(1)
        sys.path.append(res)
        import listener.processor
        self.handler = listener.processor.GenHandler
    
    def log(self, msg):
        import servicemanager
        servicemanager.LogInfoMsg(str(msg))
        def sleep(self, sec):
            win32api.Sleep(sec*1000, True)
    
    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        try:
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self.log('start')
            self.start()
            self.log('wait')
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
            self.log('done')
        except Exception, x:
            self.log('Exception : %s' % x)
            self.SvcStop()
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.log('stopping')
        self.stop()
        self.log('stopped')
        win32event.SetEvent(self.stop_event)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
    
    def parse_config(self, *args, **kwargs):
        self.config = ConfigParser.ConfigParser()
        self.config.read(self.config_filename)
    
    def setup_logging(self, *arg, **kwargs):
        '''This should always setup the logger.
        '''
        log_config = dict(self.config.items('logging', 1))
        log_config['level'] = getattr(logging, log_config['log_level'], logging.INFO)
        del log_config['log_level']
        log_config['filename'] = self.determine_filename(log_config['filename'])
        logging.basicConfig(**log_config)
        self.logger = logging.getLogger()
    
    def start(self):
        '''Kickoff the TCP Server
        
        @todo Integrate this with the Windows code. It shares so much...and gains so little
        ''' 
        self.import_handler()
        address = self.config.get('listening server', 'ipport').split(',')
        host, port = [], []
        for tmp in address:
            tmp_address, tmp_port = tmp.split(':')
            host.append(tmp_address)
            port.append(tmp_port)
        
        servers = [ abstract.ConfigHTTPServer(self.config, (host, int(port)), self.handler) for host, port in zip(host, port)]
        try:
            for server in servers:
                threading.Thread(target=server.serve_forever, args=[]).start()
        except Exception, e:
            self.logger.exception(e)
    
    def stop(self):
        pass

class PassiveService(ListenerService):
    _svc_name_ = 'NCPAPassive'
    _svc_display_name_ = 'NCPA Passive'
    _svc_description_ = 'Service that sleeps, then awakens and accesses the NCPA agent.'
    
    def __init__(self, *args, **kwargs):
        ListenerService.__init__(self, *args, **kwargs)
    
    def run_all_handlers(self, *args, **kwargs):
        '''Will run all handlers that exist.
        
        The handler must:
        - Have a config header entry
        - Abide by the handler API set forth by passive.abstract.NagiosHandler
        - Terminate in a timely fashion
        '''
        handlers = self.config.get('passive', 'handlers').split(',')
        import_basedir()
        
        import passive.nrdp
        
        for handler in handlers:
            try:
                module_name = 'passive.%s' % handler
                __import__(module_name)
                tmp_handler = sys.modules[module_name]
            except ImportError,e:
                self.logger.error('Could not import module passive.%s, skipping. %s' % (handler, str(e)))
            else:
                try:
                    ins_handler = tmp_handler.Handler(self.config)
                    ins_handler.run()
                    self.logger.debug('Successfully ran handler %s' % handler)
                except Exception, e:
                    self.logger.exception(e)
    
    def start(self, *args, **kwargs):
        '''Start the waiting loop.
        '''
        while True:
            self.parse_config()
            self.run_all_handlers()
            
            sleep = int(self.config.get('passive', 'sleep'))
            time.sleep(sleep)


def instart(cls, stay_alive=True):
    '''Install and  Start (auto) a Service
            
    @param cls Class: Class (derived from Service) that implement the Service
    @param stay_alive boolean: Service will stop on logout if False
    '''
    try:
        module_path=modules[cls.__module__].__file__
    except AttributeError:
        # Require executable from sys to compile properly
        from sys import executable
        module_path=executable
    module_file = splitext(abspath(module_path))[0]
    cls._svc_reg_class_ = '%s.%s' % (module_file, cls.__name__)
    print cls._svc_name_
    if stay_alive: 
        win32api.SetConsoleCtrlHandler(lambda x: True, True)
    try:
        win32serviceutil.InstallService(
            cls._svc_reg_class_,
            cls._svc_name_,
            cls._svc_display_name_,
            startType = win32service.SERVICE_AUTO_START
        )
        print 'Installation Suceeded...'
        win32serviceutil.StartService(
            cls._svc_name_
        )
        print 'Service Started.'
    except Exception, x:
        print str(x)
        
            
