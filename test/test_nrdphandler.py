import os
import sys
import configparser
from unittest import TestCase

# Load NCPA
sys.path.append(os.path.join(os.path.dirname(__file__), '../agent/'))
import passive.nrdp

class TestNRDPHandler(TestCase):

    def setUp(self):
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        self.config.add_section('nrdp')
        self.config.set('nrdp', 'hostname', 'testing')
        self.config.set('nrdp', 'parent', 'https://fully.qualified/')
        self.config.set('nrdp', 'token', 'testing')
        self.config.add_section('passive checks')
        self.config.set('passive checks', '%HOSTNAME%|__HOST__', '/cpu/count')
        self.config.set('passive checks', 'TESTING|TESTING', '/cpu/count')
        self.config.add_section('api')
        self.config.set('api', 'community_string', 'mytoken')
        self.n = passive.nrdp.Handler(self.config)

    def test_guess_hostname(self):
        self.config.set('nrdp', 'hostname', '')
        hostname = self.n.guess_hostname()
        self.assertTrue(hostname)

        self.config.set('nrdp', 'hostname', 'silver')
        hostname = self.n.guess_hostname()
        self.assertEqual(hostname, 'silver')
