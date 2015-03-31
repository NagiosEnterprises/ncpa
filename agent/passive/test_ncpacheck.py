import unittest
import platform
from ncpacheck import NCPACheck as nc
import ConfigParser as configparser
import os
import json
import listener.server


class TestNCPACheck(unittest.TestCase):
    def setUp(self):
        self.config = configparser.ConfigParser()
        self.config.add_section('api')
        self.config.set('api', 'community_string', 'mytoken')
        listener.server.listener.config['iconfig'] = {}

    def test_get_api_url_from_instruction(self):
        instruction = 'cpu/percent --warning 10 --critical=11'
        expected_url = '/api/cpu/percent/'
        expected_args = {'warning': '10', 'critical': '11', 'check': '1'}

        url, args = nc.get_api_url_from_instruction(instruction)
        self.assertEqual(url, expected_url)
        self.assertEqual(args, expected_args)

    def test_run(self):
        ncpa_check = nc({}, '/api/cpu/percent/', 'test_host', 'test_service')
        stdout, returncode = ncpa_check.run()

        self.assertIsInstance(stdout, unicode)
        self.assertIsInstance(returncode, unicode)

        new_check = nc({}, '/invalid/check', 'test_host', 'test_service')
        stdout, returncode = new_check.run()

        self.assertIsInstance(stdout, unicode)
        self.assertIsInstance(returncode, unicode)

    def setup_plugin(self, path, name, content):
        try:
            os.mkdir(path)
        except:
            # Expected
            pass
        plugin_path = os.path.join(path, name)
        with open(plugin_path, 'w') as plugin:
            plugin.write(content)

    @unittest.skipIf(platform.system() != 'Windows', 'Not running, not Windows')
    def test_run_powershell_plugin(self):
        self.config.add_section('plugin directives')
        abs_plugin_path = os.path.abspath('plugins/')
        self.config.set('plugin directives', 'plugin_path', abs_plugin_path)
        self.config.set('plugin directives', '.ps1', 'powershell -ExecutionPolicy Unrestricted -File $plugin_name $plugin_args')

        plugin = """
param ([string]$a, [int]$b)

Write-Host $a
exit $b
"""

        self.setup_plugin(abs_plugin_path, 'test.ps1', plugin)
        ncpa_check = nc(self.config, None, None, None)

        api_url = '/api/agent/plugin/test.ps1'
        result = ncpa_check.run_check(api_url, {})
        result_json = json.loads(result)

        self.assertIsInstance(result_json, dict)
        self.assertIn('value', result_json)
        self.assertEqual(result_json['value']['stdout'], '')
        self.assertEqual(result_json['value']['returncode'], 0)

        api_url = '/api/agent/plugin/test.ps1/Bingo'
        result = ncpa_check.run_check(api_url, {})
        result_json = json.loads(result)

        self.assertIsInstance(result_json, dict)
        self.assertIn('value', result_json)
        self.assertEqual(result_json['value']['stdout'], 'Bingo')
        self.assertEqual(result_json['value']['returncode'], 0)

        api_url = '/api/agent/plugin/test.ps1/Bingo/42'
        result = ncpa_check.run_check(api_url, {})
        result_json = json.loads(result)

        self.assertIsInstance(result_json, dict)
        self.assertIn('value', result_json)
        self.assertEqual(result_json['value']['stdout'], 'Bingo')
        self.assertEqual(result_json['value']['returncode'], 42)

    @unittest.skipIf(platform.system() == 'Windows', 'Not running, not POSIX')
    def test_run_shell_plugin(self):
        self.config.add_section('plugin directives')
        abs_plugin_path = os.path.abspath('plugins/')
        self.config.set('plugin directives', 'plugin_path', abs_plugin_path)
        self.config.set('plugin directives', '.sh', 'sh $plugin_name $plugin_args')

        plugin = "echo $1; exit $2"

        self.setup_plugin(abs_plugin_path, 'test.sh', plugin)
        ncpa_check = nc(self.config, None, None, None)

        api_url = '/api/agent/plugin/test.sh'
        result = ncpa_check.run_check(api_url, {})
        result_json = json.loads(result)

        self.assertIsInstance(result_json, dict)
        self.assertIn('value', result_json)
        self.assertEqual(result_json['value']['stdout'], '')
        self.assertEqual(result_json['value']['returncode'], 0)

        api_url = '/api/agent/plugin/test.sh/Hi There'
        result = ncpa_check.run_check(api_url, {})
        result_json = json.loads(result)

        self.assertIsInstance(result_json, dict)
        self.assertIn('value', result_json)
        self.assertEqual(result_json['value']['stdout'], 'Hi There')
        self.assertEqual(result_json['value']['returncode'], 0)

        api_url = '/api/agent/plugin/test.sh/Hi There/42'
        result = ncpa_check.run_check(api_url, {})
        result_json = json.loads(result)

        self.assertIsInstance(result_json, dict)
        self.assertIn('value', result_json)
        self.assertEqual(result_json['value']['stdout'], 'Hi There')
        self.assertEqual(result_json['value']['returncode'], 42)

    def test_run_check(self):
        api_url = '/api/cpu/percent/'
        api_args = {'check': '1'}

        ncpa_check = nc({}, None, None, None)
        result = ncpa_check.run_check(api_url, api_args)
        result_json = json.loads(result)

        self.assertIsInstance(result_json, dict)
        self.assertIn('value', result_json)
        self.assertIn('stdout', result_json['value'])
        self.assertIn('returncode', result_json['value'])

    def test_handle_agent_response(self):
        response = '{"value": {"stdout": "Hi", "returncode": 0}}'
        expected_stdout = "Hi"
        expected_returncode = "0"

        stdout, returncode = nc.handle_agent_response(response)
        self.assertEqual(expected_returncode, returncode)
        self.assertEqual(expected_stdout, stdout)

        response = '{"stdout": "Hi", "returncode": 0}'
        stdout, returncode = nc.handle_agent_response(response)
        self.assertIsNone(stdout)
        self.assertIsNone(returncode)

        invalid_json = "234   } : }{fl;"
        stdout, returncode = nc.handle_agent_response(invalid_json)
        self.assertIsNone(stdout)
        self.assertIsNone(returncode)

    def test_parse_cmdline_style_instruction(self):
        url_instruction = u'/api/bingo/ --warning 1 --critical 10'
        expected_api_url = '/api/bingo/'
        expected_api_args = {'warning': '1', 'critical': '10'}

        url, args = nc.parse_cmdline_style_instruction(url_instruction)

        self.assertEqual(url, expected_api_url)
        self.assertEqual(args, expected_api_args)

        url_instruction = u'/api/agent/plugin/test.sh/--warning/10/--critical/hi'
        expected_api_url = url_instruction
        expected_api_args = {}

        url, args = nc.parse_cmdline_style_instruction(url_instruction)

        self.assertEqual(url, expected_api_url)
        self.assertEqual(args, expected_api_args)

        url_instruction = '/api/bingo/ --warning=1 --critical 10'
        expected_api_url = '/api/bingo/'
        expected_api_args = {'warning': '1', 'critical': '10'}

        url, args = nc.parse_cmdline_style_instruction(url_instruction)

        self.assertEqual(url, expected_api_url)
        self.assertEqual(args, expected_api_args)

        url_instruction = '/api/bingo/ --warning=1 --critical 10 --delta'
        expected_api_url = '/api/bingo/'
        expected_api_args = {'warning': '1', 'critical': '10'}

        url, args = nc.parse_cmdline_style_instruction(url_instruction)

        self.assertEqual(url, expected_api_url)
        self.assertEqual(args, expected_api_args)

    def test_api_url_style_instruction(self):
        url_instruction = '/api/bingo/?warning=1&critical=10'
        expected_api_url = '/api/bingo/'
        expected_api_args = {'warning': '1', 'critical': '10'}

        url, args = nc.parse_api_url_style_instruction(url_instruction)

        self.assertEqual(url, expected_api_url)
        self.assertEqual(args, expected_api_args)

    def test_normalize_api_url(self):
        starts_with_slash_api = u'/api/cpu/percent'
        starts_with_api = u'api/cpu/percent'
        starts_with_slash_metric = u'/cpu/percent'
        starts_with_metric = u'cpu/percent'

        expected_url = starts_with_slash_api + '/'

        self.assertEqual(expected_url, nc.normalize_api_url(starts_with_slash_api))
        self.assertEqual(expected_url, nc.normalize_api_url(starts_with_slash_metric))
        self.assertEqual(expected_url, nc.normalize_api_url(starts_with_api))
        self.assertEqual(expected_url, nc.normalize_api_url(starts_with_metric))

