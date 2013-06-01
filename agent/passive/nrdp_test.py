#!/usr/bin/env python

import sys
import os
runpath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(runpath)
import unittest
import mock
import nrdp
import ConfigParser

class NagiosNRDPTestCase(unittest.TestCase):
    
    def setUp(self):
        conf = ConfigParser.ConfigParser()
        conf.read('etc/ncpa.cfg')
        
        self.nrdp = nrdp.Handler(conf)
    
    def tearDown(self):
        self.Handler = None

class MakeTagTest(NagiosNRDPTestCase):
    
    def setUp(self):
        super(MakeTagTest, self).setUp()
    
    def test_make_tag_tagname(self):
        element = self.nrdp.make_tag('test tag', 'content ! complex', {'attr1':'1', 'foo':'bar'})
        self.assertEqual(element.tagName, 'test tag')
    
    def test_make_tag_text(self):
        element = self.nrdp.make_tag('test tag', 'content ! complex', {'attr1':'1', 'foo':'bar'})
        self.assertEqual(element.firstChild.nodeValue, 'content ! complex')
    
    def test_make_tag_attribute1(self):
        element = self.nrdp.make_tag('test tag', 'content ! complex', {'attr1':'1', 'foo':'bar'})
        self.assertEqual(element.getAttribute('attr1'), '1')
    
    def test_make_tag_attribute2(self):
        element = self.nrdp.make_tag('test tag', 'content ! complex', {'attr1':'1', 'foo':'bar'})
        self.assertEqual(element.getAttribute('foo'), 'bar')

class MakeXMLTest(NagiosNRDPTestCase):

    def setUp(self):
        super(MakeXMLTest, self).setUp()
        self.nag_hostname = 'Spaces and stuff'
        self.servicename = 'Slightly complicated'
        self.stdout = 'This Worked\n'
        self.returncode = '0'
        self.check_type = 'host'
        self.nagios = mock.Mock(    nag_hostname=self.nag_hostname,
                                    nag_servicename=self.servicename,
                                    stdout=self.stdout,
                                    returncode=self.returncode,
                                    check_type=self.check_type )
        
    
    def test_make_xml_is_xml(self):
        xml = self.nrdp.make_xml(self.nagios)
        self.assertEqual(str(xml.__class__), 'xml.dom.minidom.Element')
    
    def test_make_xml_checkresult_is_root(self):
        xml = self.nrdp.make_xml(self.nagios)
        self.assertEqual(xml.tagName, 'checkresult')
    
    def test_make_xml_checkresult_is_root_service(self):
        self.nagios.check_type = 'service'
        xml = self.nrdp.make_xml(self.nagios)
        self.assertEqual(xml.tagName, 'checkresult')
    
    def test_make_xml_checkresult_has_no_text(self):
        xml = self.nrdp.make_xml(self.nagios)
        self.assertEqual(xml.firstChild.nodeValue, None)
    
    def test_make_xml_checkresult_has_no_text_service(self):
        self.nagios.check_type = 'service'
        xml = self.nrdp.make_xml(self.nagios)
        self.assertEqual(xml.firstChild.nodeValue, None)
    
    def test_make_xml_checkresult_has_hostname(self):
        xml = self.nrdp.make_xml(self.nagios)
        self.assertTrue('hostname' in [x.tagName for x in xml.childNodes])
    
    def test_make_xml_checkresult_has_hostname_service(self):
        self.nagios.check_type = 'service'
        xml = self.nrdp.make_xml(self.nagios)
        self.assertTrue('hostname' in [x.tagName for x in xml.childNodes])
    
    def test_make_xml_checkresult_has_stdout(self):
        xml = self.nrdp.make_xml(self.nagios)
        self.assertTrue('output' in [x.tagName for x in xml.childNodes])
    
    def test_make_xml_checkresult_has_stdout_service(self):
        self.nagios.check_type = 'service'
        xml = self.nrdp.make_xml(self.nagios)
        self.assertTrue('output' in [x.tagName for x in xml.childNodes])
    
    def test_make_xml_checkresult_has_state(self):
        xml = self.nrdp.make_xml(self.nagios)
        self.assertTrue('state' in [x.tagName for x in xml.childNodes])
    
    def test_make_xml_checkresult_has_state_service(self):
        self.nagios.check_type = 'service'
        xml = self.nrdp.make_xml(self.nagios)
        self.assertTrue('state' in [x.tagName for x in xml.childNodes])
    
    def test_make_xml_checkresult_has_output(self):
        xml = self.nrdp.make_xml(self.nagios)
        self.assertTrue('output' in [x.tagName for x in xml.childNodes])
    
    def test_make_xml_checkresult_has_output_service(self):
        self.nagios.check_type = 'service'
        xml = self.nrdp.make_xml(self.nagios)
        self.assertTrue('output' in [x.tagName for x in xml.childNodes])
    
    def test_make_xml_checkresult_has_servicename(self):
        xml = self.nrdp.make_xml(self.nagios)
        self.assertFalse('servicename' in [x.tagName for x in xml.childNodes])
    
    def test_make_xml_checkresult_has_servicename_service(self):
        self.nagios.check_type = 'service'
        xml = self.nrdp.make_xml(self.nagios)
        self.assertTrue('servicename' in [x.tagName for x in xml.childNodes])
    
    def test_make_xml_hostname_is_right(self):
        xml = self.nrdp.make_xml(self.nagios)
        node = [x for x in xml.childNodes if x.tagName == 'hostname'][0]
        self.assertEqual(node.firstChild.nodeValue, self.nag_hostname)
    
    def test_make_xml_hostname_is_right_service(self):
        self.nagios.check_type = 'service'
        xml = self.nrdp.make_xml(self.nagios)
        node = [x for x in xml.childNodes if x.tagName == 'hostname'][0]
        self.assertEqual(node.firstChild.nodeValue, self.nag_hostname)
    
    def test_make_xml_output_is_right(self):
        xml = self.nrdp.make_xml(self.nagios)
        node = [x for x in xml.childNodes if x.tagName == 'output'][0]
        self.assertEqual(node.firstChild.nodeValue, self.stdout)
    
    def test_make_xml_output_is_right_service(self):
        self.nagios.check_result = 'service'
        xml = self.nrdp.make_xml(self.nagios)
        node = [x for x in xml.childNodes if x.tagName == 'output'][0]
        self.assertEqual(node.firstChild.nodeValue, self.stdout)
    
    def test_make_xml_state_is_right(self):
        xml = self.nrdp.make_xml(self.nagios)
        node = [x for x in xml.childNodes if x.tagName == 'state'][0]
        self.assertEqual(node.firstChild.nodeValue, self.returncode)
    
    def test_make_xml_state_is_right_service(self):
        self.nagios.check_type = 'service'
        xml = self.nrdp.make_xml(self.nagios)
        node = [x for x in xml.childNodes if x.tagName == 'state'][0]
        self.assertEqual(node.firstChild.nodeValue, self.returncode)
    
    def test_make_xml_servicname_is_right_service(self):
        self.nagios.check_type = 'service'
        xml = self.nrdp.make_xml(self.nagios)
        node = [x for x in xml.childNodes if x.tagName == 'servicename'][0]
        self.assertEqual(node.firstChild.nodeValue, self.servicename)

class SetXMLOfCheckresults(NagiosNRDPTestCase):
    
    def test_set_xml_of_checkresults_is_document(self):
        xml = self.nrdp.set_xml_of_checkresults(self)
        self.assertEqual(str(xml.__class__), 'xml.dom.minidom.Document')
        
    def test_set_xml_of_checkresults_is_document(self):
        xml = self.nrdp.set_xml_of_checkresults(self)
        self.assertEqual(str(xml.__class__), 'xml.dom.minidom.Document')
    
    def test_sex_xml_of_checkresults_is_count(self):
        xml = self.nrdp.set_xml_of_checkresults(self)
        count = len(xml.childNodes[0].childNodes)
        self.assertEqual(count, 4)
    
if __name__ == '__main__':
    unittest.main()

