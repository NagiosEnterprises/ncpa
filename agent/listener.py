#!/usr/bin/env python
import processor
import daemons
import platform
import optparse

TCP_HANDLER = processor.MyTCPHandler
CONFIG_FILENAME = 'agent.cfg'

def parse_args():
    
    usage = '%prog [start|stop|reload]'
    
    parser = optparse.OptionParser()
    
    parser.add_option('-c', '--config', help='Config file to use.', default='agent.cfg')
    
    options, args = parser.parse_args()
    
    if not len(args) == 1 or args[0] not in ['start', 'stop', 'reload']:
        parser.error('Must give either start, stop or reload.')
    
    return options, args

if __name__ == "__main__":
    
    options, args = parse_args()
    
    if not platform.system() == 'Windows':
        daemon = daemons.posix.ListenerDaemon(config_filename=options.config, handler=TCP_HANDLER)
    else:
        daemon = daemons.windows.WindowsDaemon(config_filename=options.config, handler=TCP_HANDLER)
    
    gen_daemon = getattr(daemon, args[0])
    gen_daemon()
