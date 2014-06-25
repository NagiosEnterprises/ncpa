from unittest import TestCase
from nrds import Handler as n
import ConfigParser
import os
import utils
import tempfile
import json


class NRDSHandler(TestCase):
    def setUp(self):
        self.config = ConfigParser.ConfigParser()
        self.config.optionxform = str
        self.n = n(self.config)

    def test_run(self):
        self.fail()

    def test_get_plugin(self):
        def get_request(*args, **kwargs):
            return 'SECRET PAYLOAD'

        utils.send_request = get_request

        testing_dict = {
            'nrds_url': 'localhost',
            'nrds_os': 'NCPA',
            'nrds_token': 'token',
            'plugin_path': tempfile.gettempdir(),
            'plugin': 'pluginname'
        }

        self.n.get_plugin(**testing_dict)
        expected_abs_plugin_path = os.path.join(tempfile.gettempdir(), 'pluginname')

        self.assertTrue(os.path.isfile(expected_abs_plugin_path),
                        "Plugin was not created at testing site: %s" % expected_abs_plugin_path)

        with open(expected_abs_plugin_path, 'r') as plugin_test:
            l = plugin_test.readlines()[0].strip()
            self.assertEquals(l, 'SECRET PAYLOAD')

    def test_update_config(self):
        self.fail()

    def test_config_update_is_required(self):
        self.fail()

    def test_get_os(self):
        platform = self.n.get_os()
        self.assertIsInstance(platform, unicode)

    def test_list_missing_plugins(self):
        self.fail()

    def test_get_installed_plugins(self):
        self.fail()

    def tearDown(self):
        expected_abs_plugin_path = os.path.join(tempfile.gettempdir(), 'pluginname')
        try:
            os.unlink(expected_abs_plugin_path)
        except OSError:
            pass