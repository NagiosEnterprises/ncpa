#!/usr/bin/env python

import requests
import abstract
import xmltodict
import utils

class Handler( abstract.NagiosHandler ):
    """
    api for nrds config management
    """
    
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        
        self.token = self.config.get('nrdp', 'nrdp_token')
        self.nrdp_url = self.config.get('nrdp', 'nrdp_server')
        
    def run(self, *args, **kwargs):
        self.get_plug()
        self.fetch_config()
        
    def getplugin(self, *args, **kwargs):
        self.plugin_loc = self.config.get('plugin directives', 'plugin_path')
        
        kwargs['cmd'] = self.getplugin.__name__
        kwargs['os']  = "Chinook"
        kwargs['token'] = self.token
        
        self.url_request = utils.send_nrdp( self.nrdp_url, **kwargs )
        self.local_path_location = self.plugin_loc + kwargs['plugin']
        
        with open(self.local_path_location, 'w') as plugin:
            plugin.write(self.url_request.content)

    def getconfig(self, *args, **kwargs):
        """
        Downloads new config to
        whatever is declared as path
        """
        
        kwargs['configname'] = self.config.get('nrds', 'config_name')
        
        #http://192.168.1.102/nrdp/?token=k2suan32qt50&cmd=getconfig&configname=windows&os=Windows
        
        kwargs['cmd'] = self.getconfig.__name__
        kwargs['os']  = 'chinook'
        kwargs["token"] = self.token
        
        self.url_request = utils.send_nrdp( self.nrdp_url, **kwargs )
        print self.url_request.url
        
        print self.url_request.content
        
        #TODO validate config before saving
        if self.url_request.content != "":
            with open( self.config.file_path , 'w') as config:
                config.write(self.url_request.content)
                
    def updatenrds(self, *args, **kwargs):
        """
        takes current config version as argument and returns T or F if new config is available
        """
        
        kwargs['token'] = self.token
        kwargs['cmd'] = self.updatenrds.__name__
        kwargs['os']  = 'chinook'
        kwargs['configname'] = self.config.get( 'nrds' , 'config_name' )
        kwargs['version'] = self.config.get( 'nrds', 'config_version' )

        self.url_request = utils.send_nrdp( self.nrdp_url, **kwargs )
        
        #TODO log results for we do not have this config
        #print self.url_request.content
         
        self.config_dict = xmltodict.parse( self.url_request.content )
        self.status      = self.config_dict['result']['status']
        
        print self.status
        
        if self.status == "1":
            return True
        else:
            return False
