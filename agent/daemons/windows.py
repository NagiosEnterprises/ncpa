import pythoncom
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import SocketServer
import threading
import abstract

class WrapperDaemon(abstract.NCPADaemon):
    
    def __init__(self, handler, *args, **kwargs):
        super(WrapperDaemon, self).__init__(self, *args, **kwargs)
        self.handler = handler
    
    def run(self, *args, **kwargs):
        '''
        Kickoff the TCP Server
        ''' 
        address = self.config.get('listening server', 'ipport').split(',')
        host, port = [], []
        for tmp in address:
            tmp_address, tmp_port = tmp.split(':')
            host.append(tmp_address)
            port.append(tmp_port)
        
        servers = [ SocketServer.TCPServer((host, int(port)), self.handler) for host, port in zip(host, port)]
        try:
            for server in servers:
                threading.Thread(target=server.serve_forever, args=[]).start()
        except Exception, e:
            f.write('This was an exception.\n %s' % str(e))
            self.logger.exception(e)

class ListenerDaemon(win32serviceutil.ServiceFramework, abstract.NCPADaemon):
    
    def __init__(self, config_filename, handler, *args, **kwargs):
        win32serviceutil.ServiceFramework.__init__(self, *args, **kwargs)
        self._svc_name = 'ncpalistener'
        self._svc_display_name = 'NCPA Listener'
        self.config_filename = config_filename
        self.handler = handler
        win32serviceutil.ServiceFramework.__init__(self, *args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.main()

    def main(self):
        process = WrapperDaemon(handler=self.handler, config_filename=self.config_filename)
        process.run()