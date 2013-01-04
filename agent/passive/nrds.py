#!/usr/bin/env python

import requests
import abstract
import xmltodict
from xml.dom.minidom import Document
from xml.dom.minidom import parseString
import utils

plugin_loc ='./plugins'
path       ='../etc/ncpa_test.cfg'

class Handler( abstract.NagiosHandler ):
    """
    api for nrds config management
    """
    
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        
        token = self.config.get('nrdp', 'nrdp_token')
        nrdp_url = self.config.get('nrdp', 'nrdp_server')
        self.nrds_settings = { 'token':token, 'nrdp_url':nrdp_url }
        
    def run(self, *args, **kwargs):
        self.get_plug()
        self.fetch_config()
        
    
    def get_plug(self, *args, **kwargs):
        kwargs["cmd"] = "getplugin"
        kwargs["os"]  = "chinook"
        
        self.url_request = requests.post(
            self.nrds_settings['nrdp_url'], params=dict( self.nrds_settings.items() + kwargs.items() )
            )
            
        self.local_path_location = plugin_loc + kwargs['plugin']
        
        with open(self.local_path_locatinnecton, 'w') as plugin:
            plugin.write(self.url_request.content)


    def fetch_config(self, *args, **kwargs):
        """
        Downloads new config to
        whatever is declared as path
        """
        
        kwargs['configname'] = self.config.get('nrds', 'config_name')
        
        #http://192.168.1.102/nrdp/?token=k2suan32qt50&cmd=getconfig&configname=windows&os=Windows
        
        kwargs['cmd'] = 'getconfig'
        kwargs['os']  = 'chinook'
        kwargs["token"] = self.nrds_settings["token"]
        
        #post_this = dict( self.nrds_settings.items() + kwargs.items() )
         
        self.url_request = utils.send_nrdp( self.nrds_settings['nrdp_url'], **kwargs )

        with open(path, 'w') as config:
            config.write(self.url_request.content)
            
    def new_config(self, *args, **kwargs):
        """
        takes current config version as argument and returns T or F if new config is available
        """
        
        print self.nrds_settings
        
        kwargs['cmd'] = 'updatenrds'
        kwargs['os']  = 'chinook'
        kwargs['config_name'] = self.config.get( 'nrds' , 'config_name' )
        kwargs['config_version'] = self.config.get( 'nrds', 'config_version' )
        
        kwargs['XMLDATA']  = self.build_xml( kwargs )
        
        print kwargs['XMLDATA']
        #~ self.url_request = requests.post(
            #~ self.nrds_settings['nrdp_url'], params=dict( self.nrds_settings.items() + kwargs.items() )
            #~ )
            #~ 
        #~ print self.url_request.content
         #~ 
        #~ self.config_dict = xmltodict.parse( self.url_request.content )
        #~ self.status      = self.config_dict['result']['status']
        #~ 
        #~ if self.status == "1":
            #~ return True
        #~ else:
            #~ return False
            #~ 
        #~ with open('/tmp/config.xml', 'w') as config:
            #~ config.write(self.url_request.content)
        #~ 
        #~ #http://192.168.2.29/nrdp//?token=k2suan32qt50&cmd=updatenrds&XMLDATA=<?xml version='1.0' ?><configs><config><name>windows</name><version>0.2</version></config></configs>
        #~ 
        
    def get_available_plugins(self, *args, **kwargs):
        """takes config name as argument
        return list of plugins as defined by config file"""
        
        kwargs['cmd'] = 'getconfig'
        kwargs['os']  = 'chinook'
        
        self.url_request = requests.post(
            self.nrds_settings['nrdp_url'], params=dict( self.nrds_settings.items() + kwargs.items() )
            )
        
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
    
        
    
