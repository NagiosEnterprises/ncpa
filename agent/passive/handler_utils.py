#!/usr/bin/env python

class NagiosAssociation(object):
    
    def __init__(self, nag_host, server_address, port=None, *args, **kwargs):
        self.nag_host = nag_host
        self.server_address = server_address
        self.port = port
    

class NCPACommand(object):
    
    def __init__(self, *args, **kwargs):
        self.command = None
        self.arguments = None
        self.json = None
    
    def parse_command(self, config_command, *args, **kwargs):
        spl = config_command.split(' ', 1)
        if len(spl) == 1:
            self.command = spl[0]
        else:
            self.command = spl[0]
            self.arguments = spl[1]

def get_commands_to_query(config):
    
    commands = dict(config.items('passive checks'))
    del commands['nagios_hostname']
    ncpa_commands = []
    for command in commands:
        tmp = NCPACommand()
        tmp.parse_command(command)
        ncpa_commands.append(tmp)
    return commands
    
