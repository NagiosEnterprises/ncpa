import xml.dom.minidom
import logging
import nagioshandler
import utils
from itertools import izip
import ConfigParser


class Handler(nagioshandler.NagiosHandler):
    """
    NRDP Handler.
    """

    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)

    @staticmethod
    def make_tag(tag_name, text='', tag_attr=None):
        """
        Make a tag given a tag name, internal text and attributes.

        :param tag_name: The name of the tag, ie <tag_name>
        :type tag-name: unicode
        :param text: The text to be placed inside of the tag.
        :type text: unicode
        :param tag_attr: Attributes to be added to the tag.
        :type tag_attr: dict
        :return:
        :rtype : xml.dom.minidom.Element
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

    @staticmethod
    def make_xml(result):
        """
        Return the XML node for a Nagios check.

        :param result: Result of running the check.
        :return: Element
        :rtype: xml.dom.minidom.Element
        """
        check_result = Handler.make_tag(u'checkresult', tag_attr={u'type': result.check_type})
        hostname = Handler.make_tag(u'hostname', unicode(result.nag_hostname))
        state = Handler.make_tag(u'state', unicode(result.returncode))
        output = Handler.make_tag(u'output', unicode(result.stdout))
        if not result.check_type == u'host':
            servicename = Handler.make_tag(u'servicename', result.nag_servicename)
            check_result.appendChild(servicename)
        check_result.appendChild(hostname)
        check_result.appendChild(state)
        check_result.appendChild(output)
        return check_result

    def get_xml_of_checkresults(self):
        """
        Gets XML of all check results in NRDP config section as
        an XML document.

        :return: The XML Document to be returned to Nagios
        :rtype: xml.dom.minidom.Document
        """
        doc = xml.dom.minidom.Document()
        check_results = doc.createElement('checkresults')
        doc.appendChild(check_results)

        for command in self.checks:
            stdout, returncode = command.run()
            element = self.make_xml(result)
            check_results.appendChild(element)

        return doc

    def run(self):
        """
        Sends all the commands to the agent and then submits them
        via NRDP to Nagios.

        :return: 0 on success, 1 on error
        :rtype : int
        """
        super(Handler, self).run()

        for check in self.checks:
            
        try:
            self.submit_to_nagios()
            error = 0
        except ConfigParser.NoSectionError, e:
            error = 1
            logging.error(u'%s -- Exiting out of passive daemon cycle.' % unicode(e))
        except ConfigParser.NoOptionError, e:
            error = 1
            logging.error(u'%s -- Exiting out of cycle.' % unicode(e))
        return error

    def guess_hostname(self):
        try:
            hostname = self.config.get('nrdp', 'hostname', None)
            assert hostname
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError, AssertionError):
            logging.debug("No hostname given in the config, falling back to parent class.")
            hostname = super(Handler, self).guess_hostname()
        return hostname

    @staticmethod
    def log_result(ret_xml):
        """
        Helper function to log the XML returned by the NRDP server.

        :param ret_xml: The XML returned by the NRDP server.
        :type ret_xml: unicode
        :rtype : None
        """
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

        logging.info(u'Message from NRDP server: %s', message)
        logging.info(u'Meta output from NRDP server: %s', meta)

    def submit_to_nagios(self):
        """
        Submit the result as XML to the NRDP server.
        """
        checkresults_xml = self.get_xml_of_checkresults()
        server = self.config.get(u'nrdp', u'parent')
        token = self.config.get(u'nrdp', u'token')
        xml_data = checkresults_xml.toxml()
        logging.debug(u'XML to be submitted: %s', xml_data)
        ret_xml = utils.send_request(url=server, token=token, XMLDATA=xml_data, cmd=u'submitcheck')
        Handler.log_result(ret_xml.content)
