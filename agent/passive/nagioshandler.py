import logging
import platform
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
        self.checks = None
        logging.info('Establishing passive handler: {}'.format(self.__class__.__name__))

    def get_commands_from_config(self):
        """
        Get list of commands from the config.

        :return: dict of ncpacheck.NCPACheck objects
        :rtype: dict
        """
        logging.debug('Parsing config for passive commands...')
        commands = dict(self.config.items('passive checks'))
        ncpa_commands = []

        for name_blob, instruction in commands.items():
            try:
                hostname, servicename = name_blob.split('|', 1)
                if hostname.upper() == '%HOSTNAME%':
                    hostname = self.guess_hostname()
            except ValueError:
                logging.error("Cannot parse passive directive for %s, name malformed, skipping.", name_blob)
                continue
            ncpa_commands.append(ncpacheck.NCPACheck(instruction, hostname, servicename))

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
        generically.

        :rtype: int
        """
        self.checks = self.get_commands_from_config()
        return 0
