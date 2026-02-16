import requests
import requests.exceptions
import os
from ncpa import passive_logger as logging


def send_request(url, connection_timeout, **kwargs):
    """
    Send an HTTP POST request to given url.

    :param url: The URL we want to pull from
    :param kwargs: Extra keywords to be passed to requests.post
    :rtype: requests.models.Response
    """

    # Check for a custom CA bundle in kwargs and verify it before use
    custom_ca_bundle = None
    temp_ca_bundle = kwargs.get('ca_bundle')

    if temp_ca_bundle:
        # Verify if custom CA bundle exists and is readable
        if os.path.isfile(temp_ca_bundle) and os.access(temp_ca_bundle, os.R_OK):
            custom_ca_bundle = temp_ca_bundle
        else:
            logging.warning("CA bundle specified in kwargs is not valid or not readable: %s", temp_ca_bundle)

    if url == "/":
        logging.error("Invalid URL: '/' is not a valid URL")
        return None

    try:
        if custom_ca_bundle is not None:
            logging.info("Using custom CA bundle for SSL verification: %s", custom_ca_bundle)
            r = requests.post(url, timeout=connection_timeout, data=kwargs, verify=custom_ca_bundle, allow_redirects=True)
        else:
            logging.info("Using default certifi CA bundle for SSL verification")
            r = requests.post(url, timeout=connection_timeout, data=kwargs, verify=True, allow_redirects=True)

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
