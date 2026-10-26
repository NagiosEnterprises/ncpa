import ast
import os
import types
import unittest

SERVER_PATH = os.path.join(os.path.dirname(__file__), '../agent/listener/server.py')


def _extract_function_source(path, name):
    with open(path, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node)
    raise AssertionError('function %s not found in %s' % (name, path))


class FakeIniConfig(object):
    """Stands in for listener.config['iconfig']; only records set() calls."""

    def __init__(self):
        self.set_calls = []

    def set(self, section, option, value):
        self.set_calls.append((section, option, value))


class TestConfigWriteNoShell(unittest.TestCase):
    """
    write_to_config_and_file() used to build a `sed -i '...'` shell command
    string from a form value and run it with subprocess.run(shell=True). A
    value containing a single quote could break out of the sed command and
    inject arbitrary shell commands, reachable from /update-config/ (and the
    equivalent add-check path in /add-check/) by anyone who can establish an
    admin session, which in the default configuration (no separate admin
    password set) is anyone holding the regular API community token.

    This loads the function straight from the source file, rather than
    importing listener.server (which pulls in gevent/psutil/daemon_manager
    and expects a live NCPA install), and runs it against a real temp file.
    """

    def _load_write_to_config_and_file(self, cfg_file):
        func_src = _extract_function_source(SERVER_PATH, 'write_to_config_and_file')

        module = types.ModuleType('fake_server_module')
        module.re = __import__('re')

        class FakeListenerLogger(object):
            def debug(self, *a, **k):
                pass

            def error(self, *a, **k):
                pass

            def exception(self, *a, **k):
                pass

        module.listener_logger = FakeListenerLogger()

        class FakeEnvironment(object):
            SYSTEM = 'Linux'

        module.environment = FakeEnvironment()

        self.fake_iconfig = FakeIniConfig()

        class FakeListener(object):
            config = {'iconfig': self.fake_iconfig}

        module.listener = FakeListener()

        # The function only calls os.path.join, to build the hardcoded
        # /usr/local/ncpa/etc/ncpa.cfg path. Route that one call at our temp
        # file instead of the real system path.
        def fake_join(*parts):
            if parts == ('/', 'usr', 'local', 'ncpa', 'etc', 'ncpa.cfg'):
                return cfg_file
            return os.path.join(*parts)

        module.os = types.SimpleNamespace(path=types.SimpleNamespace(join=fake_join))

        exec(compile(func_src, SERVER_PATH, 'exec'), module.__dict__)
        return module.write_to_config_and_file

    def test_single_quote_value_is_written_literally_not_executed(self):
        cfg_dir = self.id().replace('.', '_') + '_cfgdir'
        os.makedirs(cfg_dir, exist_ok=True)
        cfg_file = os.path.join(cfg_dir, 'ncpa.cfg')
        marker_file = os.path.abspath(os.path.join(cfg_dir, 'pwned'))

        with open(cfg_file, 'w') as f:
            f.write('[api]\n')
            f.write('nrdp_token = oldvalue\n')

        write_to_config_and_file = self._load_write_to_config_and_file(cfg_file)

        # A value with a quote and a shell command, the way the old sed -i
        # command would have been broken out of: '; touch <marker>; echo '
        malicious_value = "'; touch " + marker_file + "; echo '"

        write_to_config_and_file({('api', 'nrdp_token'): malicious_value})

        with open(cfg_file) as f:
            content = f.read()

        self.assertIn(malicious_value, content, 'the value should be written to the config file as-is')
        self.assertFalse(
            os.path.exists(marker_file),
            'the quote in the value must not have broken out and run a shell command',
        )
        self.assertEqual(self.fake_iconfig.set_calls, [('api', 'nrdp_token', malicious_value)])


class TestConfigWriteSourceNoShell(unittest.TestCase):
    """
    Static guard: these two endpoints must never go back to building a shell
    command string from form data. If this starts failing, something
    reintroduced subprocess/shell usage in the config-writing paths.
    """

    def test_write_to_config_and_file_has_no_shell_usage(self):
        src = _extract_function_source(SERVER_PATH, 'write_to_config_and_file')
        self.assertNotIn('shell=True', src)
        self.assertNotIn('subprocess', src)
        self.assertNotIn('sed -i', src)

    def test_add_check_has_no_shell_usage(self):
        src = _extract_function_source(SERVER_PATH, 'add_check')
        self.assertNotIn('shell=True', src)
        self.assertNotIn('subprocess', src)
        self.assertNotIn('sed -i', src)


if __name__ == '__main__':
    unittest.main()
