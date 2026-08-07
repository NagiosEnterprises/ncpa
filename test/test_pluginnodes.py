import includes_for_tests
import configparser
import os
import shutil
import sys
import tempfile
import types
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), '../agent/'))

if os.name == 'nt':
    mock_win32serviceutil = types.ModuleType('win32serviceutil')
    mock_win32serviceutil.ServiceFramework = type('ServiceFramework', (), {})
    for module_name, module in (
        ('servicemanager', types.ModuleType('servicemanager')),
        ('win32event', types.ModuleType('win32event')),
        ('win32service', types.ModuleType('win32service')),
        ('win32serviceutil', mock_win32serviceutil),
    ):
        sys.modules.setdefault(module_name, module)

import listener.server
import listener.pluginnodes as pluginnodes


class ArgsMock(object):
    def getlist(self, key):
        return []


class TestPluginAgentNode(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = configparser.ConfigParser()
        self.config.add_section('plugin directives')
        self.config.set('plugin directives', 'plugin_path', self.temp_dir)
        self.node = pluginnodes.PluginAgentNode('plugins')
        self.args = ArgsMock()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _write_plugin(self, rel_path, content=''):
        path = os.path.join(self.temp_dir, rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as handle:
            handle.write(content)

    def test_root_plugin_not_shadowed_by_subdirectory_duplicate(self):
        self._write_plugin('get_script_dir.ps1')
        self._write_plugin('old/get_script_dir.ps1')

        plugin = self.node.accessor(
            ['get_script_dir.ps1'],
            self.config,
            'plugins/get_script_dir.ps1',
            self.args,
        )

        self.assertIsInstance(plugin, pluginnodes.PluginNode)
        self.assertEqual(
            os.path.normpath(plugin.plugin_abs_path),
            os.path.normpath(os.path.join(self.temp_dir, 'get_script_dir.ps1')),
        )

    def test_subdirectory_plugin_resolves_by_path(self):
        self._write_plugin('get_script_dir.ps1')
        self._write_plugin('old/get_script_dir.ps1')

        plugin = self.node.accessor(
            ['old', 'get_script_dir.ps1'],
            self.config,
            'plugins/old/get_script_dir.ps1',
            self.args,
        )

        self.assertIsInstance(plugin, pluginnodes.PluginNode)
        self.assertEqual(
            os.path.normpath(plugin.plugin_abs_path),
            os.path.normpath(os.path.join(self.temp_dir, 'old', 'get_script_dir.ps1')),
        )
        
    def test_walk_lists_root_and_subdirectory_plugins(self):
        self._write_plugin('check_a.sh')
        self._write_plugin('old/check_b.sh')

        result = self.node.walk(config=self.config)
        
        self.assertEqual(result['plugins'], ['check_a.sh', 'old/check_b.sh'])


if __name__ == '__main__':
    unittest.main()