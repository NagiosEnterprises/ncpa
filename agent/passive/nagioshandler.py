import platform
import passive.ncpacheck
from ncpa import passive_logger as logging


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
        :type config: configparser.ConfigParser
        :rtype: None
        """
        self.config = config
        self.checks = None
        self.next_run = None

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
                        duration = self.config.getint('passive', 'sleep')
                    except Exception:
                        duration = 300

                if hostname.upper() == '%HOSTNAME%':
                    hostname = self.guess_hostname()
            except ValueError:
                logging.error("Cannot parse passive directive for %s, name malformed, skipping.", name_blob)
                continue
            ncpa_commands.append(passive.ncpacheck.NCPACheck(self.config, instruction, hostname, servicename, duration))

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

    def set_next_run(self, delay_interval):
        """
        Set the next run time based on the delay interval.

        :param delay_interval: The delay interval in seconds before the next run.
        :type delay_interval: int
        :rtype: None
        """
        import time
        self.next_run = time.time() + delay_interval

    def needs_to_run(self, delay_interval):
        """
        Check if the handler needs to run based on the delay interval.

        :param delay_interval: The delay interval in seconds between runs.
        :type delay_interval: int
        :return: True if it's time to run, False otherwise.
        :rtype: bool
        """
        import time
        if not hasattr(self, 'next_run'):
            self.set_next_run(0)
            return True
        if time.time() >= self.next_run:
            self.set_next_run(delay_interval)
            return True
        return False

