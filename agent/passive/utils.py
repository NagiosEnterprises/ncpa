import requests
import configparser
import logging

class PConfigParser(configparser.ConfigParser):
    
    def __init__(self, *args, **kwargs):
        configparser.ConfigParser.__init__(self, *args, **kwargs)
    
    def read(self, file_path, *args, **kwargs):
        self.file_path = file_path
        configparser.ConfigParser.read(self, file_path, *args, **kwargs)

def send_request(url, *args, **kwargs):
    r = requests.get(url, params=kwargs, verify=False, allow_redirects=True)
    logging.debug('hitting url with payload: %s' % str(r.url))
    logging.debug('content response from payload: %s' % str(r.content))
    return r
