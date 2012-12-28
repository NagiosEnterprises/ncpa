import abstract
import sys
import SocketServer
import logging
import os
import time
import signal

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
        super(PassiveDaemon, self).__init__(*args, **kwargs)

class ListenerDaemon(PosixDaemon):
    '''
    This kicks off the TCP listener.
    '''
    
    def __init__(self, *args, **kwargs):
        self.PIDFILE = 'var/ncpa.pid'
        super(ListenerDaemon, self).__init__(*args, **kwargs)
    
    def start(self, *args, **kwargs):
        '''
        Kickoff the TCP Server
        '''
        
        self.check_pid(self.PIDFILE)
       
        HOST = self.config.get('listening server', 'ip')
        PORT = int(self.config.get('listening server', 'port'))
        
        self.logger.info('Starting TCP Server on %s:%d', HOST, PORT)
        server = SocketServer.TCPServer((HOST, PORT), self.handler)
        self.draw_spinner('Daemonizing...')
        daemonize()
        self.write_pid(self.PIDFILE, os.getpid())
        try:
            server.serve_forever()
        except Exception, e:
            self.logger.exception(e)
    
    def stop(self, *args, **kwargs):
        '''
        Stop the TCP Server.
        '''
        super(stop, self).stop(self.PIDFILE, *args, **kwargs)
