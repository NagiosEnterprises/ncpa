import requests
import requests.exceptions
import os
import certifi
from ncpa import passive_logger as logging


def send_request(url, connection_timeout, **kwargs):
    """
    Send an HTTP POST request to given url.

    :param url: The URL we want to pull from
    :param kwargs: Extra keywords to be passed to requests.post
    :rtype: requests.models.Response
    """

    # This will print the path to the CA bundle file
    logging.info(f"Requests CA bundle path: {requests.certs.where()}")

    # Print the value of the environment variable (might be None if not set)
    logging.info(f"REQUESTS_CA_BUNDLE env var: {os.environ.get('REQUESTS_CA_BUNDLE')}")

    # Print the path to certifi's CA bundle
    logging.info(f"Certifi CA bundle path: {certifi.where()}")

    # Path to your custom CA bundle file
    custom_ca_bundle_path = '/tmp/ca-bundle.pem'
    os.environ['REQUESTS_CA_BUNDLE'] = custom_ca_bundle_path

    # Verify using custom CA bundle
    logging.info(f"Updated CA bundle path: {requests.certs.where()}")

    # Verify os.environ is set correctly
    logging.info(f"Updated REQUESTS_CA_BUNDLE env var: {os.environ.get('REQUESTS_CA_BUNDLE')}")
    
    if url == "/":
        logging.error("Invalid URL: '/' is not a valid URL")
        return None

    try:
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
