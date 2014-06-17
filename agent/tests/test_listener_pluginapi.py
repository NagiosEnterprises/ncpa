import unittest
import sys
import os

sys.path.append(os.path.dirname(__file__) + '/..')
from listener.pluginapi import *


class TestGetCmdline(unittest.TestCase):
    def test_get_cmdline(self):
        self.assertEqual([u'cmd', u'/c', u'a', u'b'], get_cmdline(u'a', [u'b'], u'cmd /c $plugin_name $plugin_args'))
        self.assertEqual([u'cmd', u'/c /d', u'a', u'b'], get_cmdline(u'a', [u'b'], u'cmd "/c /d" $plugin_name $plugin_args'))
        self.assertEqual([u'cmd', u'/c', u'a', u'b', u'c'], get_cmdline(u'a', [u'b', u'c'], u'cmd /c $plugin_name $plugin_args'))

        self.assertEqual([u'a', u'b'], get_cmdline(u'a', [u'b'], u'$plugin_name $plugin_args'))
        self.assertEqual([u'a', u'b', u'c', u'test spaces'], get_cmdline(u'a', [u'b', u'c', u'test spaces'], u'$plugin_name $plugin_args'))


class TestDeltaizeCall(unittest.TestCase):
    def test_deltaize_call(self):
        mock_key_name = u'testing-key'
        filename = u"ncpa-%s.tmp" % unicode(hash(mock_key_name))
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
        self.assertEqual(False, is_within_range(u'10', 0))
        self.assertEqual(False, is_within_range(u'10', 10))
        self.assertEqual(False, is_within_range(u'10', 5))
        self.assertEqual(True, is_within_range(u'10', 20))
        self.assertEqual(True, is_within_range(u'10', -1))

        #Test normal string <int>:<int>
        self.assertEqual(False, is_within_range(u'10:20', 10))
        self.assertEqual(False, is_within_range(u'10:20', 20))
        self.assertEqual(False, is_within_range(u'10:20', 15))
        self.assertEqual(True, is_within_range(u'10:20', 1))
        self.assertEqual(True, is_within_range(u'10:20', 21))

        #Test <int>:, so anything less than 20 should be True
        self.assertEqual(False, is_within_range(u'20:', 21))
        self.assertEqual(False, is_within_range(u'20:', 20))
        self.assertEqual(True, is_within_range(u'20:', 10))
        self.assertEqual(True, is_within_range(u'20:', 0))

        #Test normal string <int>:<int>
        self.assertEqual(True, is_within_range(u'@10:20', 10))
        self.assertEqual(True, is_within_range(u'@10:20', 20))
        self.assertEqual(True, is_within_range(u'@10:20', 15))
        self.assertEqual(False, is_within_range(u'@10:20', 1))
        self.assertEqual(False, is_within_range(u'@10:20', 21))


class TestGetPluginInstructions(unittest.TestCase):
    def test_get_plugin_instructions(self):
        mock_config = ConfigParser.ConfigParser()
        mock_config.add_section(u'plugin directives')
        mock_config.set(u'plugin directives', u'.exe', u'cmd /c $plugin_name $plugin_args')
        mock_plugin = u'test.exe'

        self.assertEqual(u'cmd /c $plugin_name $plugin_args', get_plugin_instructions(mock_plugin, mock_config))
        self.assertEqual(u'$plugin_name $plugin_args', get_plugin_instructions(u'test.sh', mock_config))


class TestExecutePlugin(unittest.TestCase):
    def test_execute_plugin(self):
        test_plugin_filename = os.path.join(tempfile.gettempdir(), u'testing_plugin.sh')
        test_plugin_fd = open(test_plugin_filename, u'w')
        test_plugin_fd.write(u'#!/bin/sh\n')
        test_plugin_fd.write(u'echo hi $1\n')
        test_plugin_fd.write(u'exit 1')
        test_plugin_fd.close()

        os.chmod(test_plugin_filename, 0777)

        config = ConfigParser.ConfigParser()
        config.add_section(u'plugin directives')
        config.set(u'plugin directives', u'plugin_path', tempfile.gettempdir())

        result = execute_plugin(u'testing_plugin.sh', [u'hi'], config)
        os.unlink(test_plugin_filename)

        expected = {u'returncode': 1, u'stdout': u'hi hi'}
        self.assertEqual(result, expected)


if __name__ == u'__main__':
    unittest.main()
