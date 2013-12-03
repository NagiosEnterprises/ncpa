import unittest

class TestTryBoth(unittest.TestCase):
    def test_try_both(self):
        # self.assertEqual(expected, try_both(plugin_name, plugin_args, config))
        assert False # TODO: implement your test here

class TestGetCmdlineInstruct(unittest.TestCase):
    def test_get_cmdline_instruct(self):
        # self.assertEqual(expected, get_cmdline_instruct(plugin_name, plugin_args, instruction))
        assert False # TODO: implement your test here

class TestGetCmdlineNoInstruct(unittest.TestCase):
    def test_get_cmdline_no_instruct(self):
        # self.assertEqual(expected, get_cmdline_no_instruct(plugin_name, plugin_args))
        assert False # TODO: implement your test here

class TestDeltaizeCall(unittest.TestCase):
    def test_deltaize_call(self):
        # self.assertEqual(expected, deltaize_call(keyname, result))
        assert False # TODO: implement your test here

class TestMakePluginResponseFromAccessor(unittest.TestCase):
    def test_make_plugin_response_from_accessor(self):
        # self.assertEqual(expected, make_plugin_response_from_accessor(accessor_response, accessor_args))
        assert False # TODO: implement your test here

class TestIsWithinRange(unittest.TestCase):
    def test_is_within_range(self):
        # self.assertEqual(expected, is_within_range(nagstring, value))
        assert False # TODO: implement your test here

class TestExecutePlugin(unittest.TestCase):
    def test_execute_plugin(self):
        # self.assertEqual(expected, execute_plugin(plugin_name, plugin_args, config, *args, **kwargs))
        assert False # TODO: implement your test here

if __name__ == '__main__':
    unittest.main()
