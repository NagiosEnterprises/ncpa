import requests
import logging


def send_request(url, **kwargs):
    """
    Send an HTTP POST request to given url.

    :param url: The URL we want to pull from
    :param kwargs: Extra keywords to be passed to requests.post
    :rtype: requests.models.Response
    """
    r = requests.post(url, data=kwargs, verify=False, allow_redirects=True)
    logging.debug('Content response from URL: %s' % r.content)
    return r.content
