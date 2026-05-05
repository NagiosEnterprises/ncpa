import requests
import requests.exceptions
import os
import subprocess
from ncpa import passive_logger as logging

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

    try:
        r = requests.post(url, timeout=connection_timeout, data=kwargs, verify=True, allow_redirects=True)
        # logging.debug('Content response from URL: %s' % str(r.content))
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


def restart_ncpa_service():
    # allow_restart = config.get('general', 'allow_remote_restart').lower()
    allow_restart = 1

    logging.debug("Restarting NCPA service...")

    if allow_restart in {'none', '0'}:
        logging.info("restart not allowed")
    else:
        try:
            logging.info("allow_restart: %s", allow_restart)
            if os.name == 'nt':
                logging.info("restarting ncpa service")
                subprocess.run(["net", "stop", "ncpa"], check=False)
                time.sleep(5)
                subprocess.run(["net", "start", "ncpa"], check=True)
            elif os.name == 'posix':
                logging.info("restarting ncpa service")
                subprocess.run(["sudo", "systemctl", "restart", "ncpa.service"], check=True)
            else:
                logging.error("unsupported OS")
                return False
        except Exception as e:
            logging.exception(e)
            return False

    logging.debug("Successfully restarted NCPA service")