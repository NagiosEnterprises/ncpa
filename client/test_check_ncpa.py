#!/usr/bin/env python

import unittest
import mock
import re

# The module to be tested
import check_ncpa


#~ Django URL validator
def is_valid_url(url):
    regex = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url)


class Test(unittest.TestCase):
    
    def setUp(self):
        self.c_options = mock.MagicMock()
        self.c_options.token = 'mytoken'
        self.c_options.hostname = 'bingo.bongo.com'
        self.c_options.unit = None
        self.c_options.arguments = '-t this -b foo/bar'
        self.c_options.warning = '10'
        self.c_options.critical = '20'
        self.c_options.delta = True
        self.c_options.metric = '/cpu/percentage'
        self.c_options.port = 1025
    
    def test_run_check(self):
        results = check_ncpa.run_check({'returncode': 0, 'stdout': 'Hi'})
        self.assertEquals(len(results), 2)
        self.assertEquals(results, ('Hi', 0))
    
    def test_show_list(self):
        results = check_ncpa.show_list({'Bingo': 'bongo'})
        self.assertEquals(len(results), 2)
    
    #~ Non-TDD tests, just development correctness tests
    
    def test_get_host_part_from_options(self):
        host_part = check_ncpa.get_host_part_from_options(self.c_options)
        self.assertEquals(str, type(host_part))
        self.assertTrue('https' in host_part)
        self.assertTrue(is_valid_url(host_part))
        
        host_part = check_ncpa.get_host_part_from_options(self.c_options)
        self.assertEquals(str, type(host_part))
        self.assertTrue('http' in host_part)
        self.assertTrue(is_valid_url(host_part))
    
    def test_get_arguments_from_options(self):
        arguments = check_ncpa.get_arguments_from_options(self.c_options)
        self.assertEquals(str, type(arguments))
        self.assertTrue(arguments)
        self.assertTrue('unit' not in arguments)
        
        self.c_options.list = True
        arguments = check_ncpa.get_arguments_from_options(self.c_options)
        self.assertTrue(arguments)
        self.assertEquals(str, type(arguments))
        self.assertFalse('delta' in arguments)
        self.assertFalse('arguments' in arguments)

    def test_get_check_arguments_from_options(self):
        arguments = check_ncpa.get_check_arguments_from_options(self.c_options)
        self.assertTrue(arguments)
        self.assertIn('%2f', arguments.lower())
    
    def test_get_url_from_options(self):
        url = check_ncpa.get_url_from_options(self.c_options)
        self.assertEquals(str, type(url))
        self.assertTrue(is_valid_url(url))

if __name__ == '__main__':
    unittest.main()
