#!/usr/bin/env python

import requests
from xml.dom.minidom import Document

class nrds():
    def __init__(self, token, nrdp_url):
        self.nrds_settings = { 'token':token, 'nrdp_url':nrdp_url } 
    
    def get_plug(self, *args, **kwargs):
        kwargs["cmd"] = "getplugin"
        kwargs["os"]  = "chinook"
        
        self.url_request = requests.post(
            self.nrds_settings['nrdp_url'], params=dict( self.nrds_settings.items() + kwargs.items() )
            )
            
        self.local_path_location = self.nrds_settings['plugin_loc'] + kwargs['plugin']
        
        with open(self.local_path_location, 'w') as plugin:
            plugin.write(self.url_request.content)


    def fetch_config(self, *args, **kwargs):
        kwargs['cmd'] = 'updatenrds'
        
        doc = Document()
        configs = doc.createElement("configs")
        doc.appendChild(configs)
        config = doc.createElement("config")
        configs.appendChild(config)
        name = doc.createElement("name")
        config.appendChild(name)
        name_text = doc.createTextNode(kwargs['config_name'])
        name.appendChild(name_text)
        version = doc.createElement("version")
        config.appendChild(version)
        version_number = doc.createTextNode(kwargs['config_version'])
        version.appendChild(version_number)

        kwargs['XMLDATA'] = doc.toprettyxml(indent="")
        
        self.url_request = requests.post(
            self.nrds_settings['nrdp_url'], params=dict( self.nrds_settings.items() + kwargs.items() )
            )
        
        with open(kwargs['path'], 'w') as config:
            config.write(self.url_request.content)

        #top = http://192.168.2.29/nrdp//?token=k2suan32qt50&cmd=updatenrds&XMLDATA=<?xml version='1.0' ?><configs><config><name>windows</name><version>0.2</version></config></configs>
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
    
        
    
