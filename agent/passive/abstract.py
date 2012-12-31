import logging

logger = logging.getLogger()

class NagiosHandler(object):
    '''
    These are intended for use to handle passive checks.
    
    Establishes the API for querying a passive agent to submit this 
    directly.
    '''
    def __init__(self, config, *args, **kwargs):
        '''
        Does initial such as parsing the config.
        '''
        logger.debug('Establishing Nagios handler...')
        self.config = config
        self.parse_config()
        logger.debug('Nagios handler established.')
    
    def _parse_commands(self, *args, **kwargs):
        '''
        Grab the commands from the config.
        '''
        commands = dict(self.config.items('passive checks'))
        self.ncpa_commands = []
        for command in commands:
            host_service = command
            raw_command = commands[command]
            tmp = NCPACommand()
            tmp.set_host_and_service(host_service)
            tmp.parse_command(raw_command)
            logger.debug(tmp)
            self.ncpa_commands.append(tmp)
            
    
    def set_association(self, *args, **kwargs):
        '''
        Setup contact info for the Nagios Server.
        '''
        raise Exception('Abstract call to _set_association().')
    
    def parse_config(self, *args, **kwargs):
        '''
        Grab the commands from the config.
        '''
        self._parse_commands()

class NagiosAssociation(object):
    
    def __init__(self, nag_host, server_address, port=None, *args, **kwargs):
        self.server_address = server_address
        self.port = port

class NCPACommand(object):
    
    def __init__(self, *args, **kwargs):
        self.nag_hostname = None
        self.nag_servicename = None
        self.command = None
        self.arguments = None
        self.json = None
    
    def __repr__(self):
        builder  = 'Nagios Hostname: %s -- ' % self.nag_hostname
        builder += 'Nagios Servicename: %s -- ' % self.nag_servicename 
        builder += 'Command: %s -- ' % self.command
        builder += 'Arguments: %s' % self.arguments
        return builder
    
    def set_host_and_service(self, directive, *args, **kwargs):
        '''
        Given the directive name in the config, such as:
        
        localhost|CPU Usage
        
        This should set the hostname and servicename to localhost and
        CPU Usage, respectively.
        '''
        self.nag_hostname, self.nag_servicename = directive.split('|')
        logger.debug('Setting hostname to %s and servicename to %s' % (self.nag_hostname, self.nag_servicename))
    
    def parse_command(self, config_command, *args, **kwargs):
        '''
        Parses the actual command from the config file. Example
        
        check_memory
        
        Should set self.command to check_memory, anything in a space
        after it should be regarded as arguments.
        '''
        logger.debug('Parsing command: %s' % config_command)
        try:
            self.command, self.arguments = config_command.split(' ', 1)
            logger.debug('Command contained arguments.')
        except ValueError:
            self.command = config_command
            logger.debug('Command did not contain arguments. Single directive.')
