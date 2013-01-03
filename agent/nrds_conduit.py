#!/usr/bin/env python

import requests
import xmltodict
from xml.dom.minidom import Document
from xml.dom.minidom import parseString

class nrds():
    """
    api for nrds config management
    """
    
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
        
        #http://192.168.1.102/nrdp/?token=e9c6oudjfjs6&cmd=getconfig&configname=windows&os=Windows&os_ver=5.1.2600&arch=x86
        
        kwargs['cmd'] = 'getconfig'
        kwargs['os']  = 'chinook'
        kwargs['configname'] = 'ncpa'
        
        self.url_request = requests.post(
            self.nrds_settings['nrdp_url'], params=dict( self.nrds_settings.items() + kwargs.items() )
            )
            
        with open(kwargs['path'], 'w') as config:
            config.write(self.url_request.content)
            
    def new_config(self, *args, **kwargs):
        kwargs['cmd'] = 'updatenrds'
        kwargs['os']  = 'chinook'
        kwargs['config_name'] = 'ncpa'
        
        kwargs['XMLDATA']  = self.build_xml( kwargs )
        
        self.url_request = requests.post(
            self.nrds_settings['nrdp_url'], params=dict( self.nrds_settings.items() + kwargs.items() )
            )
            
        #~ print self.url_request.content
         
        self.config_dict = xmltodict.parse( self.url_request.content )
        self.status      = self.config_dict['result']['status']
        
        if self.status == "1":
            return True
        else:
            return False
        #~ 
        with open('/tmp/config.xml', 'w') as config:
            config.write(self.url_request.content)
        #~ 
        #~ #http://192.168.2.29/nrdp//?token=k2suan32qt50&cmd=updatenrds&XMLDATA=<?xml version='1.0' ?><configs><config><name>windows</name><version>0.2</version></config></configs>
        #~ 
    def build_xml(self, settings_dict):
        
        doc = Document()
        configs = doc.createElement("configs")
        doc.appendChild(configs)
        config = doc.createElement("config")
        configs.appendChild(config)
        name = doc.createElement("name")
        config.appendChild(name)
        name_text = doc.createTextNode(settings_dict['config_name'])
        name.appendChild(name_text)
        version = doc.createElement("version")
        config.appendChild(version)
        version_number = doc.createTextNode(settings_dict['config_version'])
        version.appendChild(version_number)
        
        return doc.toprettyxml(indent="")
        
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
    
        
    
