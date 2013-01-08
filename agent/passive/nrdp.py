import abstract
import lxml.etree as etree
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
    
    def make_hostcheck_xml(self, result, *args, **kwargs):
        '''
        Return the XML node for a host check
        '''
        checkresult = etree.Element('checkresult', attrib = {'type' : 'host'})
        hostname = etree.SubElement(checkresult, 'hostname')
        hostname.text = result.nag_hostname
        state = etree.SubElement(checkresult, 'state')
        state.text = str(result.returncode)
        output = etree.SubElement(checkresult, 'output')
        output.text = result.stdout
        return checkresult
    
    def make_servicecheck_xml(self, result, *args, **kwargs):
        '''
        Return the XML node for a host check
        '''
        checkresult = etree.Element('checkresult', attrib = {'type' : 'service'})
        hostname = etree.SubElement(checkresult, 'hostname')
        hostname.text = result.nag_hostname
        servicename = etree.SubElement(checkresult, 'servicename')
        servicename.text = result.nag_servicename
        state = etree.SubElement(checkresult, 'state')
        state.text = str(result.returncode)
        output = etree.SubElement(checkresult, 'output')
        output.text = result.stdout
        return checkresult
    
    def set_xml_of_checkresults(self, *args, **kwargs):
        '''
        Get XML of all check results in NRDP.
        '''
        root = etree.Element('checkresults')
        for result in self.ncpa_commands:
            if result.check_type == 'host':
                root.append(self.make_hostcheck_xml(result))
            else:
                root.append(self.make_servicecheck_xml(result))
        self.checkresults = etree.ElementTree(root)
    
    def run(self, *args, **kwargs):
        '''
        Sends all the commands to the agent and then submits them
        via NRDP to Nagios.
        '''
        import ConfigParser
        try:
            self.send_all_commands()
            self.submit_to_nagios()
        except ConfigParser.NoSectionError, e:
            logger.error('%s -- Exiting out of passive daemon cycle.' % str(e))
        except ConfigParser.NoOptionError, e:
            logger.error('%s -- Exiting out of cycle.' % str(e))
    
    def log_result(self, retxml, *args, **kwargs):
        tree = etree.fromstring(retxml)
        message = tree.find('./message')
        meta = tree.find('./meta/output')
        if message is not None:
            logger.info('Message from NRDP server: %s' % message.text)
        else:
            logger.error('Improper XML returned from NRDP server.')
        if meta is not None:
            logger.info('Meta output from NRDP server: %s' % meta.text)
        else:
            logger.error('No meta information returned from NRDP server.')
    
    def submit_to_nagios(self, *args, **kwargs):
        '''
        Submit the result as XML to the NRDP server.
        '''
        self.set_xml_of_checkresults()
        server = self.config.get('nrdp', 'parent')
        token = self.config.get('nrdp', 'token')
        xmldata = etree.tostring(self.checkresults)
        retxml = utils.send_nrdp(url=server, token=token, XMLDATA=xmldata, cmd='submitcheck')
        self.log_result(retxml.content)
        
