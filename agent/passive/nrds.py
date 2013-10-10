#!/usr/bin/env python
import requests
import sys
import abstract
import xml.etree.ElementTree as ET
import utils
import json
import re
import logging
import os

class Handler(abstract.NagiosHandler):
    """
    api for nrds config management
    """
    
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
            
    def run(self, *args, **kwargs):
        if self.config_update_is_required():
            logging.debug('Updating my NRDS config...')
            self.update_config()
        
        needed_plugins = self.list_missing_plugins()
        if needed_plugins:
            logging.debug('We need some plugins. Getting them...')
            for plugin in needed_plugins:
                self.get_plugin(plugin)
        logging.debug('Done with this NRDS iteration.')
        
    def get_plugin(self, plugin, *args, **kwargs):
        nrds_url = self.config.get('nrdp', 'parent')
        plugin_path = self.config.get('plugin directives', 'plugin_path')
        token = self.config.get('nrds', 'TOKEN')
        operating_sys = self.get_os()
        
        getargs = {     'cmd':      'getplugin',
                        'os':       operating_sys,
                        'token':    token,
                        'plugin':   plugin,
                }
        
        url_request = utils.send_request(nrds_url, **getargs)
        local_path_location = os.path.join(plugin_path, plugin)
        
        logging.debug( "Downloading plugin to location: %s" % str(local_path_location))
        
        try:
            with open(local_path_location, 'w') as plugin_file:
                plugin_file.write(url_request.content)
                os.chmod(local_path_location, 0775)
        except IOError:
            logging.error('Could not write the plugin to %s, perhaps permissions went bad.', local_path_location)

    def update_config(self, *args, **kwargs):
        '''Downloads new config to whatever is declared as path
        
        @todo Validate config before saving
        '''
        nrdp_url = self.config.get('nrdp', 'parent')
        
        get_args = {    'configname': self.config.get('nrds', 'CONFIG_NAME'),
                        'cmd': 'getconfig',
                        'os': 'NCPA',
                        'token': self.config.get('nrds', 'TOKEN') }
        
        logging.debug('URL I am requesting: %s' % nrdp_url)
        url_request = utils.send_request(nrdp_url, **get_args)
        
        if url_request.content != "":
            try:
                with open(self.config.file_path , 'w') as config:
                    config.write(url_request.content)
            except IOError:
                logging.error('Could not rewrite the config. Permissions my be wrong.')
            else:
                logging.info('Successfully updated NRDS config.')
        
        
                
    def config_update_is_required(self, *args, **kwargs):
        '''Returns true or false based on value in the config_version
        variable in the config
        
        @todo Log results if we do not have this config
        '''
        get_args = {    'token':        self.config.get('nrdp', 'token'),
                        'cmd':          'updatenrds',
                        'os':           'NCPA',
                        'configname':   self.config.get('nrds', 'CONFIG_NAME'),
                        'version':      self.config.get('nrds', 'CONFIG_VERSION'), }
        
        logging.debug('Connecting to NRDS server...')
        
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
            status = 0
        
        return bool(status)
    
    def get_os(self):
        plat = sys.platform
        
        if plat == 'darwin' or plat == 'mac':
            os = 'Darwin'
        elif 'linux' in plat:
            os = 'Linux'
        elif 'aix' in plat:
            os = 'AIX'
        elif 'sun' in plat:
            os = 'SunOS'
        elif 'win' in plat:
            os = 'Windows'
        else:
            os = 'Generic'
        return os
        
    def list_missing_plugins(self, *args, **kwargs):
        installed_plugins = self.get_installed_plugins()
        required_plugins = self.get_required_plugins()
        return required_plugins - installed_plugins
        
    def get_required_plugins(self, *args, **kwargs):
        passive_checks = self.config.items('passive checks')
        filtered = [x[1] for x in passive_checks if '|' in x[0] and 'plugin/' in x[1]]
        PLUGIN_NAME = re.compile(r'plugin/([^/]+).*')
        return frozenset([PLUGIN_NAME.search(x).group(1) for x in filtered])
    
    def get_installed_plugins(self, *args, **kwargs):
        logging.warning(self.config.get('plugin directives', 'plugin_path'))
        return frozenset([x for x in os.listdir(self.config.get('plugin directives', 'plugin_path')) if not x.startswith('.')])
