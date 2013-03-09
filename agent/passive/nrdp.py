#!/usr/bin/env python

import abstract
import xml.dom.minidom
import logging
import utils

logger = logging.getLogger()

class NRDPAssociation(abstract.NagiosAssociation):
    '''
    Specialized Association that has NRDP variables.
    '''
    
    def __init__(self, *args, **kwargs):
        super(NRDPAssociation, self).__init__(*args, **kwargs)
        self.server_address = kwargs.get('server_address', None)
        self.token = kwargs.get('token', None)

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
            for k,v in zip(tagattr.keys(), tagattr.values()):
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
            checkresul.appendChild(servicename)
        checkresult.appendChild(hostname)
        checkresult.appendChild(state)
        checkresult.appendChild(output)
        return checkresult
    
    def set_xml_of_checkresults(self, *args, **kwargs):
        '''
        Get XML of all check results in NRDP.
        '''
        doc = xml.dom.minidom.Document()
        checkresults = doc.createElement('checkresults')
        doc.appendChild(checkresults)
        for result in self.ncpa_commands:
            element = self.make_xml(result)
            checkresults.appendChild(element)
        return doc
    
    #~ def run(self, *args, **kwargs):
        #~ '''
        #~ Sends all the commands to the agent and then submits them
        #~ via NRDP to Nagios.
        #~ '''
        #~ import ConfigParser
        #~ try:
            #~ self.send_all_commands()
            #~ self.submit_to_nagios()
        #~ except ConfigParser.NoSectionError, e:
            #~ logger.error('%s -- Exiting out of passive daemon cycle.' % str(e))
        #~ except ConfigParser.NoOptionError, e:
            #~ logger.error('%s -- Exiting out of cycle.' % str(e))
    #~ 
    #~ def log_result(self, retxml, *args, **kwargs):
        #~ tree = etree.fromstring(retxml)
        #~ message = tree.find('./message')
        #~ meta = tree.find('./meta/output')
        #~ if message is not None:
            #~ logger.info('Message from NRDP server: %s' % message.text)
        #~ else:
            #~ logger.error('Improper XML returned from NRDP server.')
        #~ if meta is not None:
            #~ logger.info('Meta output from NRDP server: %s' % meta.text)
        #~ else:
            #~ logger.error('No meta information returned from NRDP server.')
    #~ 
    #~ def submit_to_nagios(self, *args, **kwargs):
        #~ '''
        #~ Submit the result as XML to the NRDP server.
        #~ '''
        #~ self.set_xml_of_checkresults()
        #~ server = self.config.get('nrdp', 'parent')
        #~ token = self.config.get('nrdp', 'token')
        #~ xmldata = etree.tostring(self.checkresults)
        #~ retxml = utils.send_request(url=server, token=token, XMLDATA=xmldata, cmd='submitcheck')
        #~ self.log_result(retxml.content)
        
if __name__ == "__main__":
    import ConfigParser
    conf = ConfigParser.ConfigParser()
    conf.read('../etc/ncpa.cfg')
    a = Handler(conf)
    b = object()
    b.stdout = 'hi'
    b.state = 'the state'
    b.output = 'the output'
    a.make_hostcheck_xml(b)
