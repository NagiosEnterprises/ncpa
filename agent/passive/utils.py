import requests
import ConfigParser
import logging

class PConfigParser(ConfigParser.ConfigParser):
    
    def __init__(self, *args, **kwargs):
        ConfigParser.ConfigParser.__init__(self, *args, **kwargs)
    
    def read(self, file_path, *args, **kwargs):
        self.file_path = file_path
        ConfigParser.ConfigParser.read(self, file_path, *args, **kwargs)

def send_request(url, *args, **kwargs):
    r = requests.post(url, data=kwargs, verify=False, allow_redirects=True)
    logging.debug('hitting url with payload: %s' % str(r.url))
    logging.debug('content response from payload: %s' % str(r.content))
    return r
