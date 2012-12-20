import abstract
import sys
import SocketServer
import logging
import os
import time
import signal

class PosixDaemon(abstract.NCPADaemon):
    
    def __init__(self, *args, **kwargs):
        super(PosixDaemon, self).__init__(*args, **kwargs)
    
    def check_pid(self, *args, **kwargs):
        '''
       Make sure there is no pid file that is designated for
       this process.
       '''
        try:
            f = open('var/ncpa.pid')
            f.close()
            print 'ncpa.pid still exists, ncpa process must still be running.'
            self.logger.warning('User attempted to restart, var/ncpa.pid still exists, exiting.')
            sys.exit(1)
        except IOError:
            return False
    
    def write_pid(self, pid, *args, **kwargs):
        '''
       Write the PID to the ncpa.pid file
       '''
        f = open('var/ncpa.pid', 'w')
        f.write(str(pid))
        f.close()
    
    def start(self, *args, **kwargs):
        '''
       Kickoff the TCP Server
       '''
        self.check_pid()
       
        HOST = self.config.get('listening server', 'ip')
        PORT = int(self.config.get('listening server', 'port'))
        
        self.logger.info('Starting TCP Server on %s:%d', HOST, PORT)
        server = SocketServer.TCPServer((HOST, PORT), self.handler)
        self.draw_spinner('Daemonizing...')
        daemonize()
        self.write_pid(os.getpid())
        try:
            server.serve_forever()
        except Exception, e:
            self.logger.exception(e)
    
    def stop(self, *args, **kwargs):
        '''
       Stop the TCP Server.
       '''
        try:
            f = open('var/ncpa.pid', 'r')
        except IOError:
            print 'No pid file exists. Cannot terminate.'
            sys.exit(1)
        ncpa_pid = f.read()
        f.close()
        os.kill(int(ncpa_pid), signal.SIGTERM)
        self.draw_spinner('Terminating')
        os.remove('var/ncpa.pid')
    
    def reload(self, *args, **kwargs):
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
