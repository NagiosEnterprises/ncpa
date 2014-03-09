import logging
import json
import platform
import urllib.request, urllib.parse, urllib.error
import listener.server
import optparse
import shlex


class NagiosHandler(object):
    """These are intended for use to handle passive activities.
    
    Provides common functions that would be necessary for
    periodic activities that get kicked off by the passive NCPA
    daemon.

    """
    def __init__(self, config, *args, **kwargs):
        """Does initial such as parsing the config.

        """
        self.ncpa_commands = None
        self.config = None

        self.parse_config(config)

        logging.debug('Establishing Nagios handler...')
    
    def _parse_commands(self, *args, **kwargs):
        """Grab the commands from the config.

        """
        logging.debug('Parsing commands...')
        commands = dict(self.config.items('passive checks'))
        self.ncpa_commands = []
        for command in commands:
            if '|' not in command:
                continue 
            logging.debug('Parsing new individual command.')
            host_service = command
            raw_command = commands[command]
            tmp = NCPACommand(self.config)
            tmp.set_host_and_service(host_service)
            tmp.parse_command(raw_command)
            logging.debug("Command to be run: %s" % tmp)
            self.ncpa_commands.append(tmp)

    @staticmethod
    def get_warn_crit_from_arguments(arguments):
        logging.debug('Parsing arguments: %s' % arguments)
        #~ Must give the arguments a prog name in order for them to work with
        #~ optparse
        arguments = str('./xxx ' + arguments)
        parser = optparse.OptionParser()
        parser.add_option('-w', '--warning')
        parser.add_option('-c', '--critical')
        parser.add_option('-u', '--unit')
        try:
            arg_lat = shlex.split(arguments)
            logging.debug("String args: %s" % str(arg_lat))
            options, args = parser.parse_args(arg_lat)
        except Exception as e:
            logging.exception(e)
        warning = options.warning or ''
        critical = options.critical or ''
        unit = options.unit or ''
        return {'warning': warning, 'critical': critical, 'unit': unit}
    
    def send_command(self, ncpa_command, *args, **kwargs):
        """Query the local active agent.

        """
        url = ncpa_command.command
        if ncpa_command.arguments and not 'plugin' in ncpa_command.command:
            wcu_dict = NagiosHandler.get_warn_crit_from_arguments(ncpa_command.arguments)
            url += '?' + urllib.parse.urlencode(wcu_dict)
        if 'plugin' in ncpa_command.command and ncpa_command.arguments:
            url += '/' + ncpa_command.arguments
        response = listener.server.internal_api(url, self.config)
        logging.debug("Response from server: %s" % response)
        return response
        
    def send_all_commands(self, *args, **kwargs):
        """Sends all commands

        """
        for command in self.ncpa_commands:
            tmp_result = self.send_command(command)
            command.set_json(tmp_result)
    
    def parse_config(self, config, *args, **kwargs):
        """Grab the commands from the config.

        """
        self.config = config
        logging.debug('Parsing config...')
        self._parse_commands()
    
    def run(self, *args, **kwargs):
        """This item is a convenience method to consist with the API of a
        handler that is expected to exist in order to be called
        generically.

        """
        self.send_all_commands()


class NCPACommand(object):
    
    def __init__(self, config=None, *args, **kwargs):
        self.nag_hostname = None
        self.nag_servicename = None
        self.command = None
        self.arguments = None
        self.json = None
        self.stdout = None
        self.returncode = None
        self.check_type = None
        self.config = config

    def __repr__(self):
        builder  = 'Nagios Hostname: %s -- ' % self.nag_hostname
        builder += 'Nagios Servicename: %s -- ' % self.nag_servicename 
        builder += 'Command: %s -- ' % self.command
        builder += 'Arguments: %s -- ' % self.arguments
        builder += 'Stdout: %s -- ' % self.stdout
        builder += 'Return Code: %s' % str(self.returncode)
        return builder
    
    def set_json(self, json_data, *args, **kwargs):
        """Accepts the returned JSON and turns it into the stdout and
        return code.

        """
        self.json = json_data
        self.stdout = json_data.get('stdout', 'Error parsing the JSON.')
        self.returncode = json_data.get('returncode', 'Error parsing the JSON.')
    
    def set_host_and_service(self, directive, *args, **kwargs):
        """Given the directive name in the config, such as:

        localhost|CPU Usage

        This should set the hostname and servicename to localhost and
        CPU Usage, respectively.

        """
        self.nag_hostname, self.nag_servicename = directive.split('|')
        if self.nag_servicename == '__HOST__':
            self.check_type = 'host'
        else:
            self.check_type = 'service'
        if self.nag_hostname in ['%HOSTNAME%', '%hostname%']:
            self.nag_hostname = self.guess_hostname()
        logging.debug('Setting hostname to %s and servicename to %s' % (self.nag_hostname, self.nag_servicename))
    
    def parse_result(self, result, *args, **kwargs):
        """Parse the json result.

        """
        parsed_result = json.loads(result)
        self.stdout = parsed_result.get('stdout', 3)
        self.returncode = parsed_result.get('returncode', 'An error occurred parsing the JSON')
    
    def parse_command(self, config_command, *args, **kwargs):
        """Parses the actual command from the config file. Example
        
        check_memory
        
        Should set self.command to check_memory, anything in a space
        after it should be regarded as arguments.

        """
        logging.debug('Parsing command: %s' % config_command)
        try:
            self.command, self.arguments = config_command.split(' ', 1)
            logging.debug('Command contained arguments.')
        except ValueError:
            self.command = config_command
            logging.debug('Command did not contain arguments. Single directive.')
            
    def guess_hostname(self):
        try:
            hostname = self.config.get('nrdp', 'hostname')
            logging.debug('Using the config directive for the hostname: %s' % hostname)
        except:
            hostname = platform.node()
            logging.debug('Using the platform node name: %s' % hostname)
        return hostname