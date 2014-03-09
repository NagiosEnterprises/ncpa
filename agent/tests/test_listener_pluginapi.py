import unittest
import os
import configparser
import sys
import tempfile

sys.path.append(os.path.dirname(__file__) + '/..')
from listener.pluginapi import *


class TestGetCmdline(unittest.TestCase):
    def test_get_cmdline(self):
        self.assertEqual(['cmd', '/c', 'a', 'b'], get_cmdline('a', ['b'], 'cmd /c $plugin_name $plugin_args'))
        self.assertEqual(['cmd', '/c /d', 'a', 'b'], get_cmdline('a', ['b'], 'cmd "/c /d" $plugin_name $plugin_args'))
        self.assertEqual(['cmd', '/c', 'a', 'b', 'c'], get_cmdline('a', ['b', 'c'], 'cmd /c $plugin_name $plugin_args'))

        self.assertEqual(['a', 'b'], get_cmdline('a', ['b'], '$plugin_name $plugin_args'))
        self.assertEqual(['a', 'b', 'c', 'test spaces'], get_cmdline('a', ['b', 'c', 'test spaces'], '$plugin_name $plugin_args'))


class TestDeltaizeCall(unittest.TestCase):
    def test_deltaize_call(self):
        mock_key_name = 'testing-key'
        filename = "ncpa-%s.tmp" % str(hash(mock_key_name))
        tmpfile = os.path.join(tempfile.gettempdir(), filename)
        if os.path.isfile(tmpfile):
            os.unlink(tmpfile)
        self.assertEquals([0.0], deltaize_call(mock_key_name, [1]))
        self.assertNotEquals([0.0], deltaize_call(mock_key_name, [2]))
        os.unlink(tmpfile)


class TestMakePluginResponseFromAccessor(unittest.TestCase):
    def test_make_plugin_response_from_accessor(self):
        # self.assertEqual(expected, make_plugin_response_from_accessor(accessor_response, accessor_args))
        assert False # TODO: implement your test here


class TestIsWithinRange(unittest.TestCase):
    def test_is_within_range(self):
        #Test the normal string, <int>
        self.assertEqual(False, is_within_range('10', 0))
        self.assertEqual(False, is_within_range('10', 10))
        self.assertEqual(False, is_within_range('10', 5))
        self.assertEqual(True, is_within_range('10', 20))
        self.assertEqual(True, is_within_range('10', -1))

        #Test normal string <int>:<int>
        self.assertEqual(False, is_within_range('10:20', 10))
        self.assertEqual(False, is_within_range('10:20', 20))
        self.assertEqual(False, is_within_range('10:20', 15))
        self.assertEqual(True, is_within_range('10:20', 1))
        self.assertEqual(True, is_within_range('10:20', 21))

        #Test <int>:, so anything less than 20 should be True
        self.assertEqual(False, is_within_range('20:', 21))
        self.assertEqual(False, is_within_range('20:', 20))
        self.assertEqual(True, is_within_range('20:', 10))
        self.assertEqual(True, is_within_range('20:', 0))

        #Test normal string <int>:<int>
        self.assertEqual(True, is_within_range('@10:20', 10))
        self.assertEqual(True, is_within_range('@10:20', 20))
        self.assertEqual(True, is_within_range('@10:20', 15))
        self.assertEqual(False, is_within_range('@10:20', 1))
        self.assertEqual(False, is_within_range('@10:20', 21))


class TestGetPluginInstructions(unittest.TestCase):
    def test_get_plugin_instructions(self):
        mock_config = configparser.ConfigParser()
        mock_config.add_section('plugin directives')
        mock_config.set('plugin directives', '.exe', 'cmd /c $plugin_name $plugin_args')
        mock_plugin = 'test.exe'

        self.assertEqual('cmd /c $plugin_name $plugin_args', get_plugin_instructions(mock_plugin, mock_config))
        self.assertEqual('$plugin_name $plugin_args', get_plugin_instructions('test.sh', mock_config))


class TestExecutePlugin(unittest.TestCase):
    def test_execute_plugin(self):
        test_plugin_filename = os.path.join(tempfile.gettempdir(), 'testing_plugin.sh')
        test_plugin_fd = open(test_plugin_filename, 'w')
        test_plugin_fd.write('#!/bin/sh\n')
        test_plugin_fd.write('echo hi $1\n')
        test_plugin_fd.write('exit 1')
        test_plugin_fd.close()

        os.chmod(test_plugin_filename, 0o777)

        config = configparser.ConfigParser()
        config.add_section('plugin directives')
        config.set('plugin directives', 'plugin_path', tempfile.gettempdir())

        result = execute_plugin('testing_plugin.sh', ['hi'], config)
        os.unlink(test_plugin_filename)

        expected = {'returncode': 1, 'stdout': 'hi hi'}
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
