#!/usr/bin/env python

from urllib import urlencode
import urllib
import requests

class nrds():
    def __init__(self, token, nrdp_url, plugin_loc="./plugins/", os="Chinook"):
        
        self.nrds_settings = { 'token':token, 'nrdp_url':nrdp_url, 'plugin_loc':plugin_loc, 'os':os } 
    
    def get_plug(self, *args, **kwargs):
        kwargs["cmd"]   = "getplugin"
        
        self.url_request = requests.post(
            self.nrds_settings['nrdp_url'], params=dict( self.nrds_settings.items() + kwargs.items() )
            )
            
        self.local_path_location = self.nrds_settings['plugin_loc'] + kwargs['plugin']
        
        with open(self.local_path_location, 'w') as plugin:
            plugin.write(self.url_request.content)
            
    #~ def query_available_plugins(self, *args, **kwargs):
        #~ #http://192.168.2.29/nrdp//?token=k2suan32qt50&cmd=updatenrds&XMLDATA=%3C?xml%20version='1.0'%20?%3E%3Cconfigs%3E%3Cconfig%3E%3Cname%3Ewindows%3C/name%3E%3Cversion%3E0.1%3C/version%3E%3C/config%3E%3C/configs%3E
        #~ #this will fetch the config and return an array of
        #~ #available plugins
        #~ 
    #~ def update_available():
        #~ #predicate procedure which will return T or F if
        #~ #config is available
        #~ 
    #~ def fetch_config():
        #~ #will fetch updated config
        #~ 
    
        
    
