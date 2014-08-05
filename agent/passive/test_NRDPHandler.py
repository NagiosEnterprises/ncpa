from unittest import TestCase
from unittest import skip
from nrdp import Handler as nrdp
import ConfigParser
import xml.etree.ElementTree as ET
import ncpacheck
import listener.server
import utils


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
        self.n = nrdp(self.config)

    def test_make_tag(self):
        # Here I am not using xml.dom.minidom to parse because IT SUCKS. Rather I am using xml.etree.
        # One day I hope to change the underlying library in NRDP to use it, until then, we only use it in the tests :(
        check_xml = nrdp.make_tag(u'Mixed', u'Mixed Case', {'important': 'you betcha'}).toxml()
        tree = ET.fromstring(check_xml)

        self.assertEquals(tree.tag, 'Mixed')
        self.assertEquals(tree.attrib, {'important': 'you betcha'})
        self.assertEquals(tree.text, 'Mixed Case')

    def test_make_xml(self):
        hostname, servicename, instruction = 'MixedCase', 'Mixed Case', '/cpu/count'
        check = ncpacheck.NCPACheck(instruction, hostname, servicename)

        xml = nrdp.make_xml(check).toxml()
        tree = ET.fromstring(xml)
        servicename = tree.findall('servicename')[0]
        hostname = tree.findall('hostname')[0]
        stdout = tree.findall('output')[0]
        state = tree.findall('state')[0]

        self.assertEquals(tree.tag, 'checkresult')
        self.assertEquals(tree.attrib, {'type': 'service'})
        self.assertEquals(servicename.text, 'Mixed Case')
        self.assertEquals(hostname.text, 'MixedCase')
        self.assertIsNotNone(stdout)
        self.assertIsNotNone(state)

        hostname, servicename, instruction = 'testing_host', '__HOST__', '/cpu/count'
        check = ncpacheck.NCPACheck(instruction, hostname, servicename)

        xml = nrdp.make_xml(check).toxml()
        tree = ET.fromstring(xml)
        hostname = tree.findall('hostname')[0]
        stdout = tree.findall('output')[0]
        state = tree.findall('state')[0]

        self.assertEquals(tree.tag, 'checkresult')
        self.assertEquals(tree.attrib, {'type': 'host'})
        self.assertEquals(tree.findall('servicename'), [])
        self.assertEquals(hostname.text, 'testing_host')
        self.assertIsNotNone(stdout)
        self.assertIsNotNone(state)

    def test_get_xml_of_checkresults(self):
        self.n.checks = self.n.get_commands_from_config()
        checkresults = self.n.get_xml_of_checkresults(self.n.checks)

        checkresult_lat = ET.fromstring(checkresults).findall('checkresult')
        self.assertEquals(len(checkresult_lat), 2)

    def test_run(self):
        def mock_stub(*args, **kwargs):
            pass

        self.n.submit_to_nagios = mock_stub
        self.n.run()

        self.assertIsNotNone(self.n.checks)
        self.assertEquals(len(self.n.checks), 2)

    def test_guess_hostname(self):
        self.config.set('nrdp', 'hostname', '')
        hostname = self.n.guess_hostname()
        self.assertTrue(hostname)

        self.config.set('nrdp', 'hostname', 'silver')
        hostname = self.n.guess_hostname()
        self.assertEquals(hostname, 'silver')

    @skip("test_NRDPHandler.test_log_result: This is simply logging, no need for testing.")
    def test_log_result(self):
        """
        I'm really not sure how to test this, it is simply logging.
        """
        self.fail()

    def test_submit_to_nagios(self):
        def nrdp_server_mock(url, token, XMLDATA, cmd):
            checks = self.n.get_commands_from_config()
            checkresults = self.n.get_xml_of_checkresults(checks)

            expected_url = self.config.get('nrdp', 'parent')
            expected_token = self.config.get('nrdp', 'token')
            expected_xml = checkresults

            self.assertEquals(expected_url, url)
            self.assertEquals(expected_token, token)
            self.assertEquals(expected_xml, XMLDATA)
            self.assertEquals('submitcheck', cmd)

            return '<bingo></bingo>'

        utils.send_request = nrdp_server_mock
        self.n.checks = self.n.get_commands_from_config()
        checkresults = self.n.get_xml_of_checkresults(self.n.checks)
        self.n.submit_to_nagios(checkresults)

