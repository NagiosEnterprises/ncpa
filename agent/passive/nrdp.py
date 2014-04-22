import abstract
import xml.dom.minidom
import logging
import utils
from itertools import izip
try:
    import ConfigParser as configparser
except ImportError:
    import configparser

class Handler(abstract.NagiosHandler):
    u'''
    NRDP Handler.
    '''

    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)

    def make_tag(self, tagname, text=u'', tagattr={}, *args, **kwargs):
        doc = xml.dom.minidom.Document()
        element = doc.createElement(tagname)
        if tagattr:
            for k,v in izip(list(tagattr.keys()), list(tagattr.values())):
                element.setAttribute(unicode(k), unicode(v))
        if text:
            textnode = doc.createTextNode(text.strip())
            element.appendChild(textnode)
        return element


    def make_xml(self, result, *args, **kwargs):
        u'''
        Return the XML node for a host check
        '''
        doc = xml.dom.minidom.Document()
        checkresult = self.make_tag(u'checkresult', tagattr={u'type':result.check_type})
        hostname = self.make_tag(u'hostname', unicode(result.nag_hostname))
        state = self.make_tag(u'state', unicode(result.returncode))
        output = self.make_tag(u'output', unicode(result.stdout))
        if not result.check_type == u'host':
            servicename = self.make_tag(u'servicename', result.nag_servicename)
            checkresult.appendChild(servicename)
        checkresult.appendChild(hostname)
        checkresult.appendChild(state)
        checkresult.appendChild(output)
        return checkresult

    def set_xml_of_checkresults(self, *args, **kwargs):
        u'''
        Get XML of all check results in NRDP.
        '''
        self.doc = xml.dom.minidom.Document()
        checkresults = self.doc.createElement(u'checkresults')
        self.doc.appendChild(checkresults)
        for result in self.ncpa_commands:
            element = self.make_xml(result)
            checkresults.appendChild(element)

    def run(self, *args, **kwargs):
        u'''
        Sends all the commands to the agent and then submits them
        via NRDP to Nagios.
        '''
        try:
            self.send_all_commands()
            self.submit_to_nagios()
        except configparser.NoSectionError, e:
            logging.error(u'%s -- Exiting out of passive daemon cycle.' % unicode(e))
        except configparser.NoOptionError, e:
            logging.error(u'%s -- Exiting out of cycle.' % unicode(e))

    def log_result(self, retxml, *args, **kwargs):
        tree = xml.dom.minidom.parseString(retxml)

        try:
            message = tree.getElementsByTagName(u"message")[0].firstChild.nodeValue
        except IndexError:
            logging.warning(u'XML returned did not contain a message, or was malformed.')
            message = u'Nonexistent'

        try:
            meta = tree.getElementsByTagName(u"output")[0].firstChild.nodeValue
        except IndexError:
            logging.warning(u'XML returned did not contain a message, or was malformed.')
            meta = u'Nonexistent'

        logging.info(u'Message from NRDP server: %s' % message)
        logging.info(u'Meta output from NRDP server: %s' % meta)

    def submit_to_nagios(self, *args, **kwargs):
        u'''
        Submit the result as XML to the NRDP server.
        '''
        self.set_xml_of_checkresults()
        server = self.config.get(u'nrdp', u'parent')
        token = self.config.get(u'nrdp', u'token')
        xmldata = self.doc.toxml()
        logging.debug(u'XML to be submitted: %s', xmldata)
        retxml = utils.send_request(url=server, token=token, XMLDATA=xmldata, cmd=u'submitcheck')
        self.log_result(retxml.content)
