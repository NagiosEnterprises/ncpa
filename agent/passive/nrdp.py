#!/usr/bin/env python

from . import abstract
import xml.dom.minidom
import logging
from . import utils

class Handler(abstract.NagiosHandler):
    '''
    NRDP Handler.
    '''
    
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
    
    def make_tag(self, tagname, text='', tagattr={}, *args, **kwargs):
        doc = xml.dom.minidom.Document()
        element = doc.createElement(tagname)
        if tagattr:
            for k,v in zip(list(tagattr.keys()), list(tagattr.values())):
                element.setAttribute(str(k), str(v))
        if text:
            textnode = doc.createTextNode(text)
            element.appendChild(textnode)
        return element
        
    
    def make_xml(self, result, *args, **kwargs):
        '''
        Return the XML node for a host check
        '''
        doc = xml.dom.minidom.Document()
        checkresult = self.make_tag('checkresult', attr={'type':result.check_type})
        hostname = self.make_tag('hostname', str(result.nag_hostname))
        state = self.make_tag('state', str(result.returncode))
        output = self.make_tag('output', str(result.stdout))
        if not result.check_type == 'host':
            servicename = self.make_tag('servicename', result.nag_servicename)
            checkresult.appendChild(servicename)
        checkresult.appendChild(hostname)
        checkresult.appendChild(state)
        checkresult.appendChild(output)
        return checkresult
    
    def set_xml_of_checkresults(self, *args, **kwargs):
        '''
        Get XML of all check results in NRDP.
        '''
        doc = xml.dom.minidom.Document()
        self.checkresults = doc.createElement('checkresults')
        doc.appendChild(self.checkresults)
        for result in self.ncpa_commands:
            element = self.make_xml(result)
            self.checkresults.appendChild(element)
    
    def run(self, *args, **kwargs):
        '''
        Sends all the commands to the agent and then submits them
        via NRDP to Nagios.
        '''
        import configparser
        try:
            self.send_all_commands()
            self.submit_to_nagios()
        except configparser.NoSectionError as e:
            logging.error('%s -- Exiting out of passive daemon cycle.' % str(e))
        except configparser.NoOptionError as e:
            logging.error('%s -- Exiting out of cycle.' % str(e))
    
    def log_result(self, retxml, *args, **kwargs):
        tree = xml.dom.minidom.parseString(retxml)

        try:
            message = tree.getElementsByTagName("message")[0].firstChild.nodeValue
        except IndexError:
            logging.warning('XML returned did not contain a message, or was malformed.')
            message = 'Nonexistent'

        try:
            meta = tree.getElementsByTagName("output")[0].firstChild.nodeValue
        except IndexError:
            logging.warning('XML returned did not contain a message, or was malformed.')
            meta = 'Nonexistent'
        
        logging.info('Message from NRDP server: %s' % message)
        logging.info('Meta output from NRDP server: %s' % meta)
    
    def submit_to_nagios(self, *args, **kwargs):
        '''
        Submit the result as XML to the NRDP server.
        '''
        self.set_xml_of_checkresults()
        server = self.config.get('nrdp', 'parent')
        token = self.config.get('nrdp', 'token')
        xmldata = self.checkresults.toprettyxml()
        retxml = utils.send_request(url=server, token=token, XMLDATA=xmldata, cmd='submitcheck')
        self.log_result(retxml.content)
