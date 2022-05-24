import requests
import requests.exceptions
import logging


def send_request(url, connection_timeout, **kwargs):
    """
    Send an HTTP POST request to given url.

    :param url: The URL we want to pull from
    :param kwargs: Extra keywords to be passed to requests.post
    :rtype: requests.models.Response
    """
    
    try:
        r = requests.post(url, timeout=connection_timeout, data=kwargs, verify=False, allow_redirects=True)
    except requests.exceptions.HTTPError as e:
        logging.error("HTTP Error: %s", e)
    except requests.exceptions.ConnectionError as e:
        logging.error("Connection Error: %s", e)
    except requests.exceptions.Timeout as e:
        logging.error("Connection Timeout: %s", e)
    except Exception as ex:
        logging.exception(ex)
    else:
        logging.debug('Content response from URL: %s' % unicode(r.content))
        return r.content

    return None
