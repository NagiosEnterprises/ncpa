from unittest import TestCase
from ConfigParser import ConfigParser
from nagioshandler import NagiosHandler as nh
import ncpacheck


class TestNagiosHandler(TestCase):
    def setUp(self):
        config = ConfigParser()
        config.add_section('passive checks')
        config.set('passive checks', '%HOSTNAME%|PING', '/cpu/percent')
        config.set('passive checks', '%hostname%|__HOST__', '/api/cpu/percent --warning 10')
        config.set('passive checks', 'localhost|CPU Load', '/api/cpu/percent?warning=10')
        config.add_section('api')
        config.set('api', 'community_string', 'mytoken')
        self.nh = nh(config)

    def test_get_commands_from_config(self):
        commands = self.nh.get_commands_from_config()

        self.assertIsInstance(commands, list)

        for command in commands:
            self.assertIsInstance(command, ncpacheck.NCPACheck)

    def test_guess_hostname(self):
        guessed = self.nh.guess_hostname()
        self.assertIsInstance(guessed, str)

    def test_run(self):
        self.nh.run()
        self.assertIsInstance(self.nh.checks, list)
