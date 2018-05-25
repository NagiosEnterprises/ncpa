from unittest import TestCase
from unittest import skip
import ConfigParser
import os
import sys
import tempfile
import shutil

sys.path.append(os.path.dirname(__file__))

import listener
import passive
import passive.nrds


class NRDSHandler(TestCase):

    def setUp(self):
        listener.server.listener.config['iconfig'] = {}
        self.testing_plugin_dir = os.path.join(tempfile.gettempdir(), 'testing-plugins')
        shutil.rmtree(self.testing_plugin_dir, ignore_errors=True)
        self.config = ConfigParser.ConfigParser()
        self.config.optionxform = str
        self.config.file_path = os.path.join(self.testing_plugin_dir, "test.cfg")
        self.config.add_section('plugin directives')
        self.config.set('plugin directives', 'plugin_path', self.testing_plugin_dir)
        self.config.add_section('passive checks')
        self.n = passive.nrds.Handler(self.config)

        try:
            os.mkdir(self.testing_plugin_dir)
        except OSError:
            pass

    def test_get_plugin(self):
        def get_request(*args, **kwargs):
            return 'SECRET PAYLOAD'

        passive.utils.send_request = get_request
        plugin_path = self.n.config.get('plugin directives', 'plugin_path')

        testing_dict = {
            'nrds_url': 'localhost',
            'nrds_os': 'NCPA',
            'nrds_token': 'token',
            'plugin_path': plugin_path,
            'plugin': 'pluginname'
        }

        self.n.get_plugin(**testing_dict)
        expected_abs_plugin_path = os.path.join(plugin_path, 'pluginname')

        self.assertTrue(os.path.isfile(expected_abs_plugin_path),
                        "Plugin was not created at testing site: %s" % expected_abs_plugin_path)

        with open(expected_abs_plugin_path, 'r') as plugin_test:
            l = plugin_test.readlines()[0].strip()
            self.assertEquals(l, 'SECRET PAYLOAD')

    def test_config_update_is_required(self):
        def mock_request(*args, **kwargs):
            return "<result><status>0</status><message>OK</message></result>"

        passive.utils.send_request = mock_request
        update = self.n.config_update_is_required('mocked', 'mocked', 'TESTING', '.1')
        self.assertFalse(update)

        def mock_request(*args, **kwargs):
            return "<result><status>1</status><message>Config version is available</message></result>"

        passive.utils.send_request = mock_request
        update = self.n.config_update_is_required('mocked', 'mocked', 'TESTING', '.2')
        self.assertTrue(update)

        def mock_request(*args, **kwargs):
            return "<result><status>2</status><message>Config version is available</message></result>"

        passive.utils.send_request = mock_request
        update = self.n.config_update_is_required('mocked', 'mocked', 'TESTING', '.3')
        self.assertFalse(update)

    def test_update_config(self):
        def mock_request(*args, **kwargs):
            return ""

        passive.utils.send_request = mock_request
        success = self.n.update_config('', '', '')
        self.assertFalse(success)

        def mock_request(*args, **kwargs):
            return "[test]\nvalue = foobar"

        passive.utils.send_request = mock_request
        success = self.n.update_config('', '', '')
        self.assertTrue(success)

        os.unlink(self.config.file_path)

    def test_get_os(self):
        platform = self.n.get_os()
        self.assertIsInstance(platform, str)

    def test_list_missing_plugins(self):
        required_plugins = self.n.get_required_plugins()
        self.assertEquals(required_plugins, set())

        self.n.config.set('passive checks', 'bingo|bongo', '/api/plugin/foobar.py/moola')

        required_plugins = self.n.get_required_plugins()
        self.assertEquals(required_plugins, {'foobar.py'})

        self.n.config.set('passive checks', 'bogus_entry', '/api/plugin/bogus.bingo/foobar')
        required_plugins = self.n.get_required_plugins()
        self.assertEquals(required_plugins, {'foobar.py'})

    def test_get_installed_plugins(self):
        installed_plugins = self.n.get_installed_plugins()
        self.assertEquals(installed_plugins, set())

        foobar_plugin = os.path.join(self.testing_plugin_dir, 'foobar')
        with open(foobar_plugin, 'w') as _:
            installed_plugins = self.n.get_installed_plugins()
            self.assertEquals(installed_plugins, {'foobar'})

        os.unlink(foobar_plugin)

    def tearDown(self):
        shutil.rmtree(self.testing_plugin_dir, ignore_errors=True)
