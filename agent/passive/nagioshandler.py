import logging
import optparse
import platform
import shlex
import urllib
import listener.server
import ncpacheck

__author__ = 'nscott'


class NagiosHandler(object):
    """These are intended for use to handle passive activities.

    Provides common functions that would be necessary for
    periodic activities that get kicked off by the passive NCPA
    daemon.

    """
    def __init__(self, config):
        """
        :param config: The config that will reaped for checks.
        :type config: ConfigParser.ConfigParser
        :rtype: None
        """
        self.config = config
        logging.info('Establishing passive handler: {}'.format(self.__class__.__name__))

    def get_commands_from_config(self):
        """
        Get list of commands from the config.

        :return: list of nagioscheckresult.NagiosCheckResult objects
        :rtype: list
        """
        logging.debug('Parsing config for passive commands...')
        commands = dict(self.config.items('passive checks'))
        ncpa_commands = []

        for command in commands:

            if '|' not in command:
                logging.warning('Invalid command entered. Pipe (|) symbol required: %s, skipping.', command)
                continue

            logging.debug('Parsing new individual command: %s', command)
            hostname, servicename = command.split('|')
            instruction = commands[command]

            adjusted_hostname = self.get_hostname(hostname)

            tmp = ncpacheck.NCPACheck(adjusted_hostname, servicename, instruction)
            self.ncpa_commands.append(tmp)

        return ncpa_commands

    @staticmethod
    def guess_hostname():
        """
        Baseline for guessing the hostname. We just assume its the node name.

        :returns: The name to be used for passive check hostnames if __HOST__ is hostname.
        :rtype : unicode
        """
        hostname = platform.node()
        logging.debug('Using the platform node name: %s' % hostname)
        return hostname

    @staticmethod
    def get_warn_crit_from_arguments(arguments):
        logging.debug('Parsing arguments: %s', arguments)
        #~ Must give the arguments a prog name in order for them to work with
        #~ optparse
        arguments = unicode('./xxx ' + arguments)
        parser = optparse.OptionParser()
        parser.add_option('-w', '--warning')
        parser.add_option('-c', '--critical')
        parser.add_option('-u', '--unit')
        try:
            arg_lat = shlex.split(arguments)
            logging.debug('String args: %s' % unicode(arg_lat))
            options, args = parser.parse_args(arg_lat)
        except Exception, e:
            logging.exception(e)
        finally:
            warning = options.warning or ''
            critical = options.critical or ''
            unit = options.unit or ''

        return {'warning': warning,
                'critical': critical,
                'unit': unit}

    def query_local_agent(self, ncpa_command):
        """
        Query the local active agent for the metric status.

        :param ncpa_command: The command to be run against the local NCPA agent.
        :type ncpa_command: ncpacommand.NCPACommand
        :rtype: dict
        """
        api_url = ncpa_command.command
        if ncpa_command.arguments and not 'plugin' in ncpa_command.command:
            wcu_dict = NagiosHandler.get_warn_crit_from_arguments(ncpa_command.arguments)
            api_url += '?' + urllib.urlencode(wcu_dict)
        if 'plugin' in ncpa_command.command and ncpa_command.arguments:
            api_url += '/' + ncpa_command.arguments
        response = listener.server.internal_api(api_url, self.config)
        logging.debug("Response from server: %s", response)
        return response

    def query_local_agent_for_all_commands(self):
        """
        Query the local agent for commands put in the self.ncpa_commands
        variable. This usually means everything parsed out of the config.

        :rtype: None
        """
        for command in self.ncpa_commands:
            r = self.query_local_agent(command)
            command.set_json(r)

    def run(self, *args, **kwargs):
        u"""This item is a convenience method to consist with the API of a
        handler that is expected to exist in order to be called
        generically.

        """
        self.parse_config()
        self.query_local_agent_for_all_commands()