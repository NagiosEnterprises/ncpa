import abstract
import lxml.etree as etree

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
    
    def set_association(self, *args, *kwargs):
        '''
        Set the Nagios NRDP service credentials.
        '''
        mapped_dict = dict(self.config.items('nrdp'))
        self.association = NRDPAssociation(**mapped_dict)
    
    def set_xml_of_checkresults(self, *args, **kwargs):
        '''
        Get XML of all check results in NRDP.
        '''
        root = etree.Element('checkresults')
        self.checkresults = etree.ElementTree(root)
        for result in self.ncpa_commands:
            if result.check_type == 'host':
                attribs = {'type' : result.check_type}
            else:
                attribs = {'type' : result.check_type}
            checkresult = etree.SubElement(self.checkresults, 'checkresult', attrib=attribs)
            if not result.check_type == 'host':
                servicename_tag = 3
            
            
            
    
    def submit_to_nagios(self, ncpa_result, *args, **kwargs):
        '''
        Submit the result as XML to the NRDP server.
        '''
        pass
