import requests
import requests.exceptions
import urllib3.exceptions
from ncpa import passive_logger as logging

# Disable InsecureRequestWarning globally since we handle SSL verification in our send_request function 
# and want to avoid cluttering logs with warnings when SSL verification fails and we retry without it.
# Note: these messages will still be logged in ncpa_passive.log, but they should not go to /var/log/messages
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def send_request(url, connection_timeout, **kwargs):
    """
    Send an HTTP POST request to given url.

    :param url: The URL we want to pull from
    :param kwargs: Extra keywords to be passed to requests.post
    :rtype: requests.models.Response
    """

    if url == "/":
        logging.error("Invalid URL: '/' is not a valid URL")
        return None

    # Parse SSL verification flag cleanly
    ssl_val = kwargs.get('ssl_verify')
    ssl_verify = False if ssl_val in (0, '0', False) else True
    
    if not ssl_verify:
        logging.debug("SSL verification is disabled for this request.")

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
