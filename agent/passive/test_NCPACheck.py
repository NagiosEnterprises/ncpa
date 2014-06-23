from unittest import TestCase
from ncpacheck import NCPACheck as nc
import json
import listener.server


class TestNCPACheck(TestCase):
    def setUp(self):
        listener.server.listener.config['iconfig'] = {}

    def test_get_api_url_from_instruction(self):
        self.fail()

    def test_run(self):
        self.fail()

    def test_run_check(self):
        api_url = '/api/cpu/percent'
        api_args = {}

        result = nc.run_check(api_url, api_args)
        result_json = json.loads(result)

        self.assertIsInstance(result_json, dict)
        self.assertIn('value', result_json)

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
        url_instruction = '/api/bingo/ --warning 1 --critical 10'
        expected_api_url = '/api/bingo/'
        expected_api_args = {'warning': '1', 'critical': '10'}

        url, args = nc.parse_cmdline_style_instruction(url_instruction)

        self.assertEqual(url, expected_api_url)
        self.assertEqual(args, expected_api_args)

        url_instruction = '/api/agent/plugin/test.sh/--warning/10/--critical/hi'
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

        self.assertEqual(starts_with_slash_api, nc.normalize_api_url(starts_with_slash_api))
        self.assertEqual(starts_with_slash_api, nc.normalize_api_url(starts_with_slash_metric))
        self.assertEqual(starts_with_slash_api, nc.normalize_api_url(starts_with_api))
        self.assertEqual(starts_with_slash_api, nc.normalize_api_url(starts_with_metric))

