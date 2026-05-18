import requests
import requests.exceptions
from ncpa import passive_logger as logging


def send_request(url, connection_timeout, **kwargs):
    """
    Send an HTTP POST request to given url.

    :param url: The URL we want to pull from
    :param kwargs: Extra keywords to be passed to requests.post
    :rtype: requests.models.Response
    """

    try:
        ssl_verify = kwargs.get('ssl_verify')
        if ssl_verify == 0 or ssl_verify == '0' or ssl_verify is False:
            ssl_verify = False
        else:
            ssl_verify = True
    except Exception as ex:
        logging.debug("Exception detected while trying to get 'disable_ssl_verify' from kwargs")
        logging.exception(ex)
        ssl_verify = True

    if url == "/":
        logging.error("Invalid URL: '/' is not a valid URL")
        return None

    try:
        r = requests.post(url, timeout=connection_timeout, data=kwargs, verify=ssl_verify, allow_redirects=True)
        logging.debug('Content response from URL: %s' % str(r.content))
        return r.content
    except requests.exceptions.SSLError as ssl_err:
        logging.warning("SSL verification failed, retrying without verification: %s", ssl_err)


        try:
            r = requests.post(url, timeout=connection_timeout, data=kwargs, verify=False, allow_redirects=True)
            logging.debug('Content response from URL (no verify): %s' % str(r.content))
            return r.content
        except requests.exceptions.HTTPError as e:
            logging.error("HTTP Error: %s", e)
        except requests.exceptions.ConnectionError as e:
            logging.error("Connection Error: %s", e)
        except requests.exceptions.Timeout as e:
            logging.error("Connection Timeout: %s", e)
        except Exception as ex:
            logging.debug("Exception detected during retry without SSL verification")
            logging.exception(ex)
    except requests.exceptions.HTTPError as e:
        logging.error("HTTP Error: %s", e)
    except requests.exceptions.ConnectionError as e:
        logging.error("Connection Error: %s", e)
    except requests.exceptions.Timeout as e:
        logging.error("Connection Timeout: %s", e)
    except Exception as ex:
        logging.debug("Other Exception detected during request")
        logging.exception(ex)

        logging.info("Fallback request trying without SSL verification")
        try:
            r = requests.post(url, timeout=connection_timeout, data=kwargs, verify=False, allow_redirects=True)
            logging.debug('Content response from URL (no verify): %s' % str(r.content))
            return r.content
        except Exception as ex:
            logging.debug("Exception detected during fallback retry without SSL verification")
            logging.exception(ex)
    return None
