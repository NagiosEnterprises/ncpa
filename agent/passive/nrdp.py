import abstract
import xml.dom.minidom
import logging
import utils
from itertools import izip
import ConfigParser as configparser


class Handler(abstract.NagiosHandler):
    """
    NRDP Handler.
    """

    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)

    def make_tag(self, tag_name, text='', tag_attr=None, *args, **kwargs):
        """
        :param tag_name: The name of the tag, ie <tag_name>
        :type tag-name: unicode
        :param text: The text to be placed inside of the tag.
        :type text: unicode
        :param tag_attr: Attributes to be added to the tag.
        :type tag_attr: dict
        :param args:
        :param kwargs:
        :return:
        """
        if tag_attr is None:
            tag_attr = {}

        doc = xml.dom.minidom.Document()
        element = doc.createElement(tag_name)
        if tag_attr:
            for k, v in izip(list(tag_attr.keys()), list(tag_attr.values())):
                element.setAttribute(unicode(k), unicode(v))
        if text:
            text_node = doc.createTextNode(text.strip())
            element.appendChild(text_node)
        print type(element)
        return element


    def make_xml(self, result, *args, **kwargs):
        """
        Return the XML node for a host check
        """
        check_result = self.make_tag(u'checkresult', tag_attr={u'type': result.check_type})
        hostname = self.make_tag(u'hostname', unicode(result.nag_hostname))
        state = self.make_tag(u'state', unicode(result.returncode))
        output = self.make_tag(u'output', unicode(result.stdout))
        if not result.check_type == u'host':
            servicename = self.make_tag(u'servicename', result.nag_servicename)
            check_result.appendChild(servicename)
        check_result.appendChild(hostname)
        check_result.appendChild(state)
        check_result.appendChild(output)
        return check_result

    def set_xml_of_checkresults(self, *args, **kwargs):
        """
        Get XML of all check results in NRDP.
        """
        self.doc = xml.dom.minidom.Document()
        check_results = self.doc.createElement('checkresults')
        self.doc.appendChild(check_results)
        for result in self.ncpa_commands:
            element = self.make_xml(result)
            check_results.appendChild(element)

    def run(self, *args, **kwargs):
        """
        Sends all the commands to the agent and then submits them
        via NRDP to Nagios.
        """
        try:
            self.send_all_commands()
            self.submit_to_nagios()
        except configparser.NoSectionError, e:
            logging.error(u'%s -- Exiting out of passive daemon cycle.' % unicode(e))
        except configparser.NoOptionError, e:
            logging.error(u'%s -- Exiting out of cycle.' % unicode(e))

    def log_result(self, ret_xml, *args, **kwargs):
        tree = xml.dom.minidom.parseString(ret_xml)

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
        """
        Submit the result as XML to the NRDP server.
        """
        self.set_xml_of_checkresults()
        server = self.config.get(u'nrdp', u'parent')
        token = self.config.get(u'nrdp', u'token')
        xml_data = self.doc.toxml()
        logging.debug(u'XML to be submitted: %s', xml_data)
        ret_xml = utils.send_request(url=server, token=token, XMLDATA=xml_data, cmd=u'submitcheck')
        self.log_result(ret_xml.content)
