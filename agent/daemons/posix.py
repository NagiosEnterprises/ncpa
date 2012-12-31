import abstract
import sys
import SocketServer
import logging
import os
import time
import signal
import threading

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
        '''
        Kill spawned daemon gracefully
        '''
        try:
            f = open(pidfile, 'r')
        except IOError:
            print 'No pid file exists at %s. Cannot terminate.' % pidfile
            sys.exit(1)
        ncpa_pid = f.read()
        f.close()
        os.kill(int(ncpa_pid), signal.SIGTERM)
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

class PassiveDaemon(PosixDaemon):
    '''
    This daemon just reads the config, and if there is any
    instructions in the passive section, it runs those.
    '''
    
    def __init__(self, *args, **kwargs):
        self.PIDFILE = 'var/ncpa_passive.pid'
        super(PassiveDaemon, self).__init__(*args, **kwargs)
    
    def start(self, *args, **kwargs):
        '''
        Start the waiting loop.
        '''
        while True:
            
            import passive.handler_utils
            b = passive.abstract.NagiosHandler(self.config)
            sys.exit(1)
            
            
            

class ListenerDaemon(PosixDaemon):
    '''
    This kicks off the TCP listener.
    '''
    
    def __init__(self, handler, *args, **kwargs):
        self.PIDFILE = 'var/ncpa_listener.pid'
        self.handler = handler
        super(ListenerDaemon, self).__init__(*args, **kwargs)
    
    def start(self, *args, **kwargs):
        '''
        Kickoff the TCP Server
        '''
        self.check_pid(self.PIDFILE)
        
        address = self.config.get('listening server', 'ipport').split(',')
        host, port = [], []
        for tmp in address:
            tmp_address, tmp_port = tmp.split(':')
            host.append(tmp_address)
            port.append(tmp_port)
        
        servers = [ SocketServer.TCPServer((host, int(port)), self.handler) for host, port in zip(host, port)]
        self.draw_spinner('Daemonizing...')
        daemonize()
        self.write_pid(self.PIDFILE, os.getpid())
        try:
            for server in servers:
                threading.Thread(target=server.serve_forever, args=[]).start()
        except Exception, e:
            self.logger.exception(e)
    
    def stop(self, *args, **kwargs):
        '''
        Stop the TCP Server.
        '''
        super(ListenerDaemon, self).stop(self.PIDFILE, *args, **kwargs)
