#!/usr/bin/env python
import requests
import abstract
import xmltodict
import utils

class Handler(abstract.NagiosHandler):
    """
    api for nrds config management
    """
    
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)

        self.token = self.config.get('nrdp', 'token')
        self.nrdp_url = self.config.get('nrdp', 'parent')
            
    def run(self, *args, **kwargs):
        self.getconfig()
        self.getplugin()
        
    def getplugin(self, *args, **kwargs):
        self.plugin_loc = self.config.get('plugin directives', 'plugin_path')
        
        kwargs['cmd'] = self.getplugin.__name__
        kwargs['os']  = "Chinook"
        kwargs['token'] = self.token
        
        self.url_request = utils.send_request(self.nrdp_url, **kwargs)
        self.local_path_location = self.plugin_loc + kwargs['plugin']
        
        with open(self.local_path_location, 'w') as plugin:
            plugin.write(self.url_request.content)

    def getconfig(self, *args, **kwargs):
        '''Downloads new config to whatever is declared as path
        
        @todo Validate config before saving
        '''
        
        kwargs['configname'] = self.config.get('nrds', 'config_name')
        
        kwargs['cmd'] = self.getconfig.__name__
        kwargs['os']  = 'chinook'
        kwargs['token'] = self.token
        
        self.url_request = utils.send_request( self.nrdp_url, **kwargs )
        self.logger.debug('URL I am requesting: %s' % self.url_request.url)
        self.logger.debug('Content returned: %s' % self.url_request.content)
        
        if self.url_request.content != "":
            with open( self.config.file_path , 'w') as config:
                config.write(self.url_request.content)
                
    def updatenrds(self, *args, **kwargs):
        '''Takes current config version as argument and returns T or F 
        if new config is available

        @todo Log results if we do not have this config
        '''
        kwargs['token'] = self.token
        kwargs['cmd'] = 'updatenrds'
        kwargs['os']  = 'chinook'
        kwargs['configname'] = self.config.get('nrds', 'config_name')
        kwargs['version'] = self.config.get('nrds', 'config_version')

        self.url_request = utils.send_request(self.nrdp_url, **kwargs)
        
        self.config_dict = xmltodict.parse(self.url_request.content)
        self.status      = self.config_dict['result']['status']
        
        self.logger.debug('Status number of new config check: %s' % str(self.status))
        
        if self.status == "1":
            return True
        else:
            return False
