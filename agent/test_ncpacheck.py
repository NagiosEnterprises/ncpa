import unittest
import platform
import ConfigParser as configparser
import os
import json
import listener
import passive


class TestNCPACheck(unittest.TestCase):
    def setUp(self):
        self.config = configparser.ConfigParser()
        self.config.add_section('api')
        self.config.set('api', 'community_string', 'mytoken')
        listener.server.__INTERNAL__ = True
        listener.server.listener.config['iconfig'] = {}

    def test_get_api_url_from_instruction(self):
        instruction = 'cpu/percent --warning 10 --critical=11'
        expected_url = '/api/cpu/percent/'
        expected_args = {'warning': '10', 'critical': '11', 'check': '1'}

        url, args = passive.ncpacheck.NCPACheck.get_api_url_from_instruction(instruction)
        self.assertEqual(url, expected_url)
        self.assertEqual(args, expected_args)

    def test_run(self):
        ncpa_check = passive.ncpacheck.NCPACheck(self.config, '/api/cpu/percent/', 'test_host', 'test_service', 300)
        stdout, returncode = ncpa_check.run()

        self.assertIsInstance(stdout, unicode)
        self.assertIsInstance(returncode, unicode)

        new_check = passive.ncpacheck.NCPACheck(self.config, '/invalid/check', 'test_host', 'test_service', 300)
        stdout, returncode = new_check.run()

        self.assertIsInstance(stdout, unicode)
        self.assertIsInstance(returncode, unicode)

    def test_run_check(self):
        api_url = '/api/cpu/percent/'
        api_args = {'check': '1'}

        ncpa_check = passive.ncpacheck.NCPACheck(self.config, '', '', '', 0)
        result = ncpa_check.run_check(api_url, api_args)
        result_json = json.loads(result)

        self.assertIsInstance(result_json, dict)
        self.assertIn('stdout', result_json)
        self.assertIn('returncode', result_json)

    def test_handle_agent_response(self):
        response = '{ "stdout": "Hi", "returncode": 0 }'
        expected_stdout = "Hi"
        expected_returncode = "0"

        stdout, returncode = passive.ncpacheck.NCPACheck.handle_agent_response(response)
        self.assertEqual(expected_returncode, returncode)
        self.assertEqual(expected_stdout, stdout)

        invalid_json = "234   } : }{fl;"
        stdout, returncode = passive.ncpacheck.NCPACheck.handle_agent_response(invalid_json)
        self.assertIsNone(stdout)
        self.assertIsNone(returncode)

    def test_parse_cmdline_style_instruction(self):
        url_instruction = u'/api/bingo/ --warning 1 --critical 10'
        expected_api_url = '/api/bingo/'
        expected_api_args = {'warning': '1', 'critical': '10'}

        url, args = passive.ncpacheck.NCPACheck.parse_cmdline_style_instruction(url_instruction)

        self.assertEqual(url, expected_api_url)
        self.assertEqual(args, expected_api_args)

        url_instruction = u'/api/agent/plugin/test.sh/--warning/10/--critical/hi'
        expected_api_url = url_instruction
        expected_api_args = {}

        url, args = passive.ncpacheck.NCPACheck.parse_cmdline_style_instruction(url_instruction)

        self.assertEqual(url, expected_api_url)
        self.assertEqual(args, expected_api_args)

        url_instruction = '/api/bingo/ --warning=1 --critical 10'
        expected_api_url = '/api/bingo/'
        expected_api_args = {'warning': '1', 'critical': '10'}

        url, args = passive.ncpacheck.NCPACheck.parse_cmdline_style_instruction(url_instruction)

        self.assertEqual(url, expected_api_url)
        self.assertEqual(args, expected_api_args)

        url_instruction = '/api/bingo/ --warning=1 --critical 10 --delta'
        expected_api_url = '/api/bingo/'
        expected_api_args = {'warning': '1', 'critical': '10'}

        url, args = passive.ncpacheck.NCPACheck.parse_cmdline_style_instruction(url_instruction)

        self.assertEqual(url, expected_api_url)
        self.assertEqual(args, expected_api_args)

    def test_api_url_style_instruction(self):
        url_instruction = '/api/bingo/?warning=1&critical=10'
        expected_api_url = '/api/bingo/'
        expected_api_args = [('warning', '1'), ('critical', '10')]

        url, args = passive.ncpacheck.NCPACheck.parse_api_url_style_instruction(url_instruction)

        self.assertEqual(url, expected_api_url)
        self.assertEqual(args, expected_api_args)

    def test_normalize_api_url(self):
        starts_with_slash_api = u'/api/cpu/percent'
        starts_with_api = u'api/cpu/percent'
        starts_with_slash_metric = u'/cpu/percent'
        starts_with_metric = u'cpu/percent'

        expected_url = starts_with_slash_api + '/'

        self.assertEqual(expected_url, passive.ncpacheck.NCPACheck.normalize_api_url(starts_with_slash_api))
        self.assertEqual(expected_url, passive.ncpacheck.NCPACheck.normalize_api_url(starts_with_slash_metric))
        self.assertEqual(expected_url, passive.ncpacheck.NCPACheck.normalize_api_url(starts_with_api))
        self.assertEqual(expected_url, passive.ncpacheck.NCPACheck.normalize_api_url(starts_with_metric))

