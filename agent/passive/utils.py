import requests
import ConfigParser
import logging


class PConfigParser(ConfigParser.ConfigParser):
    def __init__(self, *args, **kwargs):
        ConfigParser.ConfigParser.__init__(self, *args, **kwargs)
        self.file_path = None

    def read(self, file_path, *args, **kwargs):
        self.file_path = file_path
        ConfigParser.ConfigParser.read(self, file_path, *args, **kwargs)


def send_request(url, **kwargs):
    """
    Send an HTTP POST request to given url.

    :param url: The URL we want to pull from
    :param kwargs: Extra keywords to be passed to requests.post
    :rtype: requests.models.Response
    """
    r = requests.post(url, data=kwargs, verify=False, allow_redirects=True)
    logging.debug(u'hitting url with payload: %s' % unicode(r.url))
    logging.debug(u'content response from payload: %s' % unicode(r.content))
    return r.content
