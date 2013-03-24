#!/usr/bin/env python
import requests
import abstract
import xml.etree.ElementTree as ET
import utils
import json
import logging

class Handler(abstract.NagiosHandler):
    """
    api for nrds config management
    """
    
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
            
    def run(self, *args, **kwargs):
        if self.config_update_is_required():
            self.update_config()
        #~ if self.plugin_update_is_required():
            #~ self.update_plugins()
        
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

    def update_config(self, *args, **kwargs):
        '''Downloads new config to whatever is declared as path
        
        @todo Validate config before saving
        '''
        nrdp_url = self.config.get('nrdp', 'parent')
        
        get_args = {    'configname': self.config.get('nrds', 'config_name'),
                        'cmd': 'getconfig',
                        'os': 'chinook',
                        'token': self.token }
        
        url_request = utils.send_request(nrdp_url, **get_args)
        logging.debug('URL I am requesting: %s' % url_request.url)
        
        if url_request.content != "":
            with open(self.config.file_path , 'w') as config:
                config.write(self.url_request.content)
                
    def config_update_is_required(self, *args, **kwargs):
        '''Returns true or false based on value in the config_version
        variable in the config
        
        @todo Log results if we do not have this config
        '''
        get_args = {    'token':        self.config.get('nrdp', 'token'),
                        'cmd':          'updatenrds',
                        'os':           'chinook',
                        'configname':   self.config.get('nrds', 'config_name'),
                        'version':      self.config.get('nrds', 'config_version'), }
        
        nrdp_url = self.config.get('nrdp', 'parent')
        url_request = utils.send_request(nrdp_url, **get_args)
        
        response_xml = ET.fromstring(url_request.content)
        status_xml = response_xml.findall('./status')
        
        if status_xml:
            status = status_xml[0].text
        else:
            status = "0"
        
        try:
            status = int(status)
        except Exception:
            logging.error("Unrecognized value for NRDS update returned. Got %s, excpected integer." % status)
            return False
        
        logging.debug('Value returned for new config: %d' % status)
        
        if status == 2:
            logging.warning("Server does not have a record for %s config." % self.config.get('nrds', 'config_name'))
            update = 0
        
        return bool(status)
            
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
