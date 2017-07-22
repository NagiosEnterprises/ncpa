import logging
import platform
import ncpacheck
import ConfigParser


class NagiosHandler(object):
    """
    These are intended for use to handle passive activities.

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
        self.checks = None

    def get_commands_from_config(self):
        """
        Get list of commands from the config.

        :return: dict of ncpacheck.NCPACheck objects
        :rtype: dict
        """

        logging.debug('Parsing config for passive commands...')
        commands = [x for x in self.config.items('passive checks') if x[0] not in self.config.defaults()]
        ncpa_commands = []

        for name_blob, instruction in commands:
            try:
                values = name_blob.split('|')
                hostname = values[0]
                servicename = values[1]

                if len(values) > 2:
                    duration = values[2]
                else:
                    try:
                        duration = int(self.config.get('passive', 'sleep'))
                    except Exception:
                        duration = 300

                if hostname.upper() == '%HOSTNAME%':
                    hostname = self.guess_hostname()
            except ValueError:
                logging.error("Cannot parse passive directive for %s, name malformed, skipping.", name_blob)
                continue
            ncpa_commands.append(ncpacheck.NCPACheck(self.config, instruction, hostname, servicename, duration))

        return ncpa_commands

    def guess_hostname(self):
        """
        Baseline for guessing the hostname. We just assume its the node name.

        :returns: The name to be used for passive check hostnames if __HOST__ is hostname.
        :rtype: unicode
        """
        hostname = platform.node()
        logging.debug('Using the platform node name: %s' % hostname)
        return hostname

    def run(self, *args, **kwargs):
        """
        This item is a convenience method to consist with the API of a
        handler that is expected to exist in order to be called
        generically. This sets the checks parsed from the passive portion of the config.
        """
        self.checks = self.get_commands_from_config()
