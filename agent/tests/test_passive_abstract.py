import unittest
import os
import sys
import ConfigParser

sys.path.append(os.path.dirname(__file__) + u'/..')
from passive.abstract import *


class TestNagiosHandler(unittest.TestCase):
    def test_get_warn_crit_from_arguments(self):
        test_string = u'-w 10 -c 5'
        result = NagiosHandler.get_warn_crit_from_arguments(test_string)

        self.assertEqual(result[u'warning'], u'10')
        self.assertEqual(result[u'critical'], u'5')

        test_string = u'--warning 10 --critical 5'
        result = NagiosHandler.get_warn_crit_from_arguments(test_string)

        self.assertEqual(result[u'warning'], u'10')
        self.assertEqual(result[u'critical'], u'5')

    def test__parse_commands(self):
        test_config = ConfigParser.ConfigParser()
        test_config.add_section(u'passive checks')
        test_config.set(u'passive checks', u'a|b', u'bingo')
        test_config.set(u'passive checks', u'a|c', u'bongo')
        test_config.set(u'passive checks', u'ac', u'jingle')

        nh = NagiosHandler(test_config)
        self.assertEqual(len(nh.ncpa_commands), 2)

    def test_run(self):
        # nagios_handler = NagiosHandler(config, *args, **kwargs)
        # self.assertEqual(expected, nagios_handler.run(*args, **kwargs))
        assert False # TODO: implement your test here

    def test_send_all_commands(self):
        # nagios_handler = NagiosHandler(config, *args, **kwargs)
        # self.assertEqual(expected, nagios_handler.send_all_commands(*args, **kwargs))
        assert False # TODO: implement your test here

    def test_send_command(self):
        # nagios_handler = NagiosHandler(config, *args, **kwargs)
        # self.assertEqual(expected, nagios_handler.send_command(ncpa_command, *args, **kwargs))
        assert False # TODO: implement your test here


class TestNCPACommand(unittest.TestCase):
    def test___init__(self):
        # n_cpa_command = NCPACommand(config, *args, **kwargs)
        assert False # TODO: implement your test here

    def test___repr__(self):
        # n_cpa_command = NCPACommand(config, *args, **kwargs)
        # self.assertEqual(expected, n_cpa_command.__repr__())
        assert False # TODO: implement your test here

    def test_guess_hostname(self):
        # n_cpa_command = NCPACommand(config, *args, **kwargs)
        # self.assertEqual(expected, n_cpa_command.guess_hostname())
        assert False # TODO: implement your test here

    def test_parse_command(self):
        # n_cpa_command = NCPACommand(config, *args, **kwargs)
        # self.assertEqual(expected, n_cpa_command.parse_command(config_command, *args, **kwargs))
        assert False # TODO: implement your test here

    def test_parse_result(self):
        # n_cpa_command = NCPACommand(config, *args, **kwargs)
        # self.assertEqual(expected, n_cpa_command.parse_result(result, *args, **kwargs))
        assert False # TODO: implement your test here

    def test_set_host_and_service(self):
        # n_cpa_command = NCPACommand(config, *args, **kwargs)
        # self.assertEqual(expected, n_cpa_command.set_host_and_service(directive, *args, **kwargs))
        assert False # TODO: implement your test here

    def test_set_json(self):
        # n_cpa_command = NCPACommand(config, *args, **kwargs)
        # self.assertEqual(expected, n_cpa_command.set_json(json_data, *args, **kwargs))
        assert False # TODO: implement your test here

if __name__ == u'__main__':
    unittest.main()
