import win32service
import win32serviceutil
import win32api
import win32con
import win32event
import win32evtlogutil
import os
import daemons
import threading
import logging
import sys
import inspect
import re
import ConfigParser

def import_basedir():
    agent = re.compile(r'(.*agent.?)')
    this_module = inspect.currentframe().f_code.co_filename
    res = agent.search(this_module).group(1)
    sys.path.append(res)
    
class aservice(win32serviceutil.ServiceFramework):
   
    _svc_name_ = 'NCPAListener'
    _svc_display_name_ = 'NCPA Listener'
    _svc_description = 'Service that listens on a TCP port.'
         
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)      
        self.config_filename = self.determine_filename('etc/ncpa.cfg')
        self.parse_config()
        self.setup_logging()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)                    
    
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
        try:
            import listener.server
            address = self.config.get('listening server', 'ip')
            port = int(self.config.get('listening server', 'port'))
            listener.server.listener.config['iconfig'] = self.config
            listener.server.listener.run(address, port)
            url_for('static', filename='chinook.css')
            url_for('static', filename='jquery-1.8.3.min.js')
            url_for('static', filename='jquery-ui.css')
            url_for('static', filename='jquery-ui.js')
        except Exception, e:
            self.logger.exception(e)
    
    def stop(self):
        pass
    
    def SvcDoRun(self):
        import servicemanager      
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,servicemanager.PYS_SERVICE_STARTED,(self._svc_name_, '')) 
      
        self.timeout = 3000
        self.start()
        while 1:
            # Wait for service stop signal, if I timeout, loop again
            rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
            # Check to see if self.hWaitStop happened
            if rc == win32event.WAIT_OBJECT_0:
                # Stop signal encountered
                servicemanager.LogInfoMsg("aservice - STOPPED")
                break
            else:
                servicemanager.LogInfoMsg("aservice - is alive and well")
                    
               
      
def ctrlHandler(ctrlType):
    return True
                  
if __name__ == '__main__':   
    win32api.SetConsoleCtrlHandler(ctrlHandler, True)   
    win32serviceutil.HandleCommandLine(aservice)