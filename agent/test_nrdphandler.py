import os
import sys
from unittest import TestCase
from unittest import skip
import ConfigParser
import xml.etree.ElementTree as ET

sys.path.append(os.path.dirname(__file__))

import listener
import passive
import passive.nrdp


class TestNRDPHandler(TestCase):
    def setUp(self):
        listener.server.listener.config['iconfig'] = {}
        self.config = ConfigParser.ConfigParser()
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

    def test_run(self):
        def mock_stub(*args, **kwargs):
            pass

        #self.n.submit_to_nagios = mock_stub
        #self.n.run()

        #self.assertIsNotNone(self.n.checks)
        #self.assertEquals(len(self.n.checks), 2)

    def test_guess_hostname(self):
        self.config.set('nrdp', 'hostname', '')
        hostname = self.n.guess_hostname()
        self.assertTrue(hostname)

        self.config.set('nrdp', 'hostname', 'silver')
        hostname = self.n.guess_hostname()
        self.assertEquals(hostname, 'silver')
