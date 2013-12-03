import unittest

class TestNagiosHandler(unittest.TestCase):
    def test___init__(self):
        # nagios_handler = NagiosHandler(config, *args, **kwargs)
        assert False # TODO: implement your test here

    def test_get_warn_crit_from_arguments(self):
        # nagios_handler = NagiosHandler(config, *args, **kwargs)
        # self.assertEqual(expected, nagios_handler.get_warn_crit_from_arguments(arguments))
        assert False # TODO: implement your test here

    def test_parse_config(self):
        # nagios_handler = NagiosHandler(config, *args, **kwargs)
        # self.assertEqual(expected, nagios_handler.parse_config(config, *args, **kwargs))
        assert False # TODO: implement your test here

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

class TestNagiosAssociation(unittest.TestCase):
    def test___init__(self):
        # nagios_association = NagiosAssociation(*args, **kwargs)
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

if __name__ == '__main__':
    unittest.main()
