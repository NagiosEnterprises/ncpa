#!/usr/bin/env python
import processor
import ConfigParser
import logging
import daemons
import platform
import optparse

TCP_HANDLER = processor.MyTCPHandler
CONFIG_FILENAME = 'agent.cfg'

def parse_config(config_filename):
    """
    Parse the agent.cfg config file, required, listening will not run
    without one.
    """
    config = ConfigParser.ConfigParser()
    config.read(config_filename)
    return config

def parse_args():
    
    usage = '%prog [start|stop|reload]'
    
    parser = optparse.OptionParser()
    _, args = parser.parse_args()
    
    if not len(args) == 1 or args[0] not in ['start', 'stop', 'reload']:
        parser.error('Must give either start, stop or reload.')
    
    return args[0]
    

config = parse_config(CONFIG_FILENAME)

if __name__ == "__main__":
    
    command = parse_args()
    
    if not platform.system() == 'Windows':
        daemon = daemons.posix.PosixDaemon(config, TCP_HANDLER)
    else:
        daemon = daemons.windows.WindowsDaemon(config, TCP_HANDLER)
    
    gen_daemon = getattr(daemon, command)
    gen_daemon()
