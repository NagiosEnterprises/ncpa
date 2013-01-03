#!/usr/bin/env python
import listener.processor
import daemons
import platform
import optparse

TCP_HANDLER = listener.processor.MyTCPHandler

def parse_args():
    
    usage = '%prog [start|stop|reload]'
    
    parser = optparse.OptionParser()
    
    parser.add_option('-c', '--config', help='Config file to use.', default='etc/ncpa.cfg')
    
    options, args = parser.parse_args()
    
    if not len(args) == 1 or args[0] not in ['start', 'stop', 'reload']:
        parser.error('Must only give either start, stop or reload.')
    
    return options, args

if __name__ == "__main__":
    
    if not platform.system() == 'Windows':
        options, args = parse_args()
        daemon = daemons.posix.ListenerDaemon(config_filename=options.config, handler=TCP_HANDLER)
        gen_daemon = getattr(daemon, args[0])
        gen_daemon()
    else:
        import win32serviceutil
        win32serviceutil.HandleCommandLine(daemons.windows.ListenerDaemon(config_filename=options.config, handler=TCP_HANDLER)
