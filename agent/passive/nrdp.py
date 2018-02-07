import xml.dom.minidom
import logging
import listener.server
import nagioshandler
import utils
from itertools import izip
import ConfigParser


class Handler(nagioshandler.NagiosHandler):
    """
    NRDP Handler.
    """

    def __init__(self, config, *args, **kwargs):
        super(Handler, self).__init__(config, *args, **kwargs)
        listener.server.listener.config['iconfig'] = config

    @staticmethod
    def make_tag(tag_name, text='', tag_attr=None):
        """
        Make a tag given a tag name, internal text and attributes.

        :param tag_name: The name of the tag, ie <tag_name>
        :type tag_name: unicode
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
        return element

    @staticmethod
    def make_xml(check):
        """
        Return the XML node for a Nagios check.

        :param check: The NCPACheck instance we are making into XML.
        :type
        :return: Element
        :rtype: xml.dom.minidom.Element
        """
        stdout, returncode = check.run()

        if stdout is None or returncode is None:
            logging.error("Error running check for %s|%s given the instruction: %s, skipping.",
                          check.hostname,
                          check.servicename,
                          check.instruction)

        if check.servicename == '__HOST__':
            check_type = 'host'
        else:
            check_type = 'service'

        check_result = Handler.make_tag(u'checkresult', tag_attr={'type': check_type})
        hostname = Handler.make_tag(u'hostname', unicode(check.hostname))
        state = Handler.make_tag(u'state', unicode(returncode))
        output = Handler.make_tag(u'output', unicode(stdout))

        if not check_type == 'host':
            servicename = Handler.make_tag(u'servicename', check.servicename)
            check_result.appendChild(servicename)

        check_result.appendChild(hostname)
        check_result.appendChild(state)
        check_result.appendChild(output)
        return check_result

    @staticmethod
    def get_xml_of_checkresults(doc, checks, run_time):
        """
        Gets XML of all check results in NRDP config section as
        an XML document.

        :return: The XML Document to be returned to Nagios
        :rtype: xml.dom.minidom.Document
        """
        check_results = doc.createElement('checkresults')
        doc.appendChild(check_results)

        for check in checks:
            if check.needs_to_run():
                element = Handler.make_xml(check)
                check.set_next_run(run_time)
                check_results.appendChild(element)

        return doc

    def run(self, run_time):
        """
        Sends all the commands to the agent and then submits them
        via NRDP to Nagios.

        :return: 0 on success, 1 on error
        :rtype : int
        """
        logging.debug("Establishing passive handler: NRDP")
        super(Handler, self).run()

        doc = xml.dom.minidom.Document()
        doc = Handler.get_xml_of_checkresults(doc, self.checks, run_time)

        # Verify there are any checks to send
        checks = doc.getElementsByTagName('checkresult')
        if len(checks) is 0:
            logging.debug("No NRDP checks. Skipping NRDP send.")
            return

        checkresults = doc.toxml()
        self.submit_to_nagios(checkresults)

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
            message = tree.getElementsByTagName("message")[0].firstChild.nodeValue
        except IndexError:
            logging.warning('XML returned did not contain a message, or was malformed.')
            message = 'Nonexistent'

        try:
            meta = tree.getElementsByTagName("output")[0].firstChild.nodeValue
        except IndexError:
            logging.warning('XML returned did not contain a message, or was malformed.')
            meta = 'Nonexistent'

        logging.info('Message from NRDP server: %s', message)
        logging.info('Meta output from NRDP server: %s', meta)

    def submit_to_nagios(self, checkresults):
        """
        Submit the result as XML to the NRDP server.
        :param checkresults: The XML that will be submitted back to Nagios.
        :type checkresults: xml.dom.minidom.Document
        :rtype: None
        """

        try:
            server = self.config.get('nrdp', 'parent')
            token = self.config.get('nrdp', 'token')
        except Exception as ex:
            logging.exception(ex)

        # Get the list of servers (and tokens, if available)
        servers = server.split(',')
        tokens = token.split(',')

        for i, server in enumerate(servers):

            # Grab a token, or the last token
            try:
                tmp_token = tokens[i]
                token = tmp_token
            except IndexError:
                pass

            # The POST requests don't follow redirects, so we have to make sure
            # the address is completely accurate.
            if not server.endswith('/'):
                server += '/'

            logging.debug('XML to be submitted: %s', checkresults)
            ret_xml = utils.send_request(url=server, token=token, XMLDATA=checkresults, cmd='submitcheck')

            try:
                Handler.log_result(ret_xml)
            except Exception as ex:
                logging.debug(ret_xml)
                logging.exception(ex)
