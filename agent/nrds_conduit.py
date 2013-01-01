#!/usr/bin/env python

from urllib import urlencode
import urllib
import requests

class nrds():
    def __init__(self, token, nrdp_url):
        self.token      = token
        self.nrdp_url   = nrdp_url
        self.plugin_loc = "./plugins/"
        self.os		  = "Chinook"

    def get_plug(self, *args, **kwargs):
        #print args["plugin"]
        
        kwargs["token"] = self.token
        kwargs["cmd"] = "getplugin"
        kwargs["os"]  = self.os
        print kwargs
        
        self.url_request         = requests.post(self.nrdp_url, params=kwargs)
        self.local_path_location = self.plugin_loc + kwargs['plugin']
        
        print self.url_request
        
        with open(self.local_path_location, 'w') as plugin:
            plugin.write(self.url_request.content)
            
    def query_available_plugins():
        #this will fetch the config and return an array of
        #available plugins
        
    def update_available():
        #predicate procedure which will return T or F if
        #config is available
        
    def fetch_config():
        #will fetch updated config
        
    
        
    
