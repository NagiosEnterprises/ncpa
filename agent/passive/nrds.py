#!/usr/bin/env python
import requests
import abstract
import xmltodict
import utils
import json

class Handler(abstract.NagiosHandler):
    """
    api for nrds config management
    """
    
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.token = self.config.get('nrdp', 'token')
        self.nrdp_url = self.config.get('nrdp', 'parent')
            
    def run(self, *args, **kwargs):
        if self.updatenrds:
            self.getconfig()
        self.known_plugins()
        
    def getplugin(self, *args, **kwargs):
        self.plugin_loc = self.config.get('plugin directives', 'plugin_path')
        
        kwargs['cmd'] = self.getplugin.__name__
        kwargs['os']  = "Chinook"
        kwargs['token'] = self.token
        
        self.url_request = utils.send_request(self.nrdp_url, **kwargs)
        self.local_path_location = self.plugin_loc + kwargs['plugin']
        
        self.logger.debug( "downloading plugin to location: %s" % str(self.local_path_location))
        
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
            
    def known_plugins(self, *args, **kwargs):
        self.socket = self.config.get('passive', 'connect')
        self.current_plugins = self.config.items('passive checks')
        #~ '''@ handel index error'''      
        #~ for self.plugin_dir in self.current_plugins:
            #~ self.plugin = self.plugin_dir[1]
            #~ self.logger.debug('plugin directives I know about: %s' % self.plugin)
            #~ self.known.append(self.plugin)
        
        kwargs['command'] = 'enumerate_plugins'
        
        required_plugins = [x[1] for x in self.current_plugins]
        installed_plugins_json = utils.send_request(self.socket, **kwargs).json()
        #~ self.current_plugins = self.url_request.json()
        
        #~ builtins = installed_plugins_json['builtins']
        externals = installed_plugins_json['externals'] 
        
        #~ index = self.known.index('check_memory')
        
        for plugin in externals:
            for required in required_plugins:
                if required == plugin:
                    try:
                        index = required_plugins.index(plugin)
                    except IndexError, e:
                        logging.exception(e)
                    else:
                        del required_plugins[index]
        
        for to_install in required_plugins:
            self.logger.warning('Installing %s' % (to_install,))
            #~ self.getplugin(plugin=to_install)
