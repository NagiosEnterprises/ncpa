import logging
import json
import socket

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
        logger.debug('Parsing commands...')
        commands = dict(self.config.items('passive checks'))
        self.ncpa_commands = []
        for command in commands:
            logger.debug('Parsing new individual command.')
            host_service = command
            raw_command = commands[command]
            tmp = NCPACommand()
            tmp.set_host_and_service(host_service)
            tmp.parse_command(raw_command)
            logger.debug(tmp)
            self.ncpa_commands.append(tmp)
    
    def send_command(self, ncpa_command, *args, **kwargs):
        '''
        Query the local active agent.
        '''
        logger.debug('Querying agent.')
        address = self.config.get('passive', 'connect')
        host, port = address.split(':')
        logger.debug('Config states we connect to %s' % address)
        data_string = json.dumps({  'metric'    : ncpa_command.command,
                                    'warning'   : None,
                                    'critical'  : None,
                                    'spec'      : ncpa_command.arguments })
        logger.debug('Creating socket.')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, int(port)))
        sock.sendall(data_string + "\n")
        received = sock.recv(1024)
        sock.close()
        return received
        
    def send_all_commands(self, *args, **kwargs):
        '''
        Sends all commands
        '''
        for command in self.ncpa_commands:
            tmp_result = self.send_command(command)
            command.set_json(tmp_result)
    
    def parse_config(self, *args, **kwargs):
        '''
        Grab the commands from the config.
        '''
        logging.debug('Parsing config...')
        self._parse_commands()
    
    def run(self, *args, **kwargs):
        '''
        This item is a convenience method to consist with the API of a
        handler that is expected to exist in order to be called
        generically.
        '''
        self.send_all_commands()

class NagiosAssociation(object):
    '''
    More or less a struct style object that simply makes it easier
    to keep track of the Nagios Association.
    '''
    
    def __init__(self, *args, **kwargs):
        self.server_address = kwargs.get(server_address, None)

class NCPACommand(object):
    
    def __init__(self, *args, **kwargs):
        self.nag_hostname = None
        self.nag_servicename = None
        self.command = None
        self.arguments = None
        self.json = None
        self.stdout = None
        self.returncode = None
    
    def __repr__(self):
        builder  = 'Nagios Hostname: %s -- ' % self.nag_hostname
        builder += 'Nagios Servicename: %s -- ' % self.nag_servicename 
        builder += 'Command: %s -- ' % self.command
        builder += 'Arguments: %s -- ' % self.arguments
        builder += 'Stdout: %s -- ' % self.stdout
        builder += 'Return Code: %s' % str(self.returncode)
        return builder
    
    def set_json(self, json_data, *args, **kwargs):
        '''
        Accepts the returned JSON and turns it into the stdout and
        return code.
        '''
        self.json = json_data
        tmp_json = json.loads(json_data)
        self.stdout = tmp_json.get('stdout', 'Error parsing the JSON.')
        self.returncode = tmp_json.get('returncode', 'Error parsing the JSON.')
    
    def set_host_and_service(self, directive, *args, **kwargs):
        '''
        Given the directive name in the config, such as:
        
        localhost|CPU Usage
        
        This should set the hostname and servicename to localhost and
        CPU Usage, respectively.
        '''
        self.nag_hostname, self.nag_servicename = directive.split('|')
        if self.nag_servicename == '__HOST__':
            self.check_type = 'host'
        else:
            self.check_type = 'service'
        logger.debug('Setting hostname to %s and servicename to %s' % (self.nag_hostname, self.nag_servicename))
    
    def parse_result(self, result, *args, **kwargs):
        '''
        Parse the json result.
        '''
        p_result = json.loads(result)
        self.stdout = p_result.get('stdout', 3)
        self.returncode = p_result.get('returncode', 'An error occurred parsing the JSON')
    
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
