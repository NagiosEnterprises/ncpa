from __future__ import with_statement
import sys
import xml.etree.ElementTree as ET
from passive.nagioshandler import NagiosHandler
import utils
import re
import logging
import os


class Handler(NagiosHandler):
    """
    Class for handling the passive NRDS component.
    """

    def __init__(self, config):
        self.config = config

    def run(self, *args, **kwargs):
        if self.config_update_is_required():
            logging.debug(u'Updating my NRDS config...')
            self.update_config()
        needed_plugins = self.list_missing_plugins()
        if needed_plugins:
            logging.debug(u'We need some plugins. Getting them...')
            for plugin in needed_plugins:
                self.get_plugin(plugin)
        logging.debug(u'Done with this NRDS iteration.')

    @staticmethod
    def get_plugin(nrds_url, nrds_token, nrds_os, plugin_path, plugin):
        getargs = {
            'cmd': 'getplugin',
            'os': nrds_os,
            'token': nrds_token,
            'plugin': plugin
        }

        # This plugin_abs_path should be absolute, as it is adjusted when the daemon runs.
        url_request = utils.send_request(nrds_url, **getargs)
        plugin_abs_path = os.path.join(plugin_path, plugin)

        if plugin_abs_path != os.path.abspath(plugin_abs_path):
            raise ValueError("Plugin path (%s) is not absolute, I will not continue safely.", plugin_abs_path)

        logging.debug("Downloading plugin to location: %s", plugin_abs_path)

        try:
            with open(plugin_abs_path, 'wb') as plugin_file:
                plugin_file.write(url_request)
                os.chmod(plugin_abs_path, 0775)
        except Exception as exc:
            logging.error('Could not write the plugin to %s: %r', plugin_abs_path, exc)

    @staticmethod
    def update_config(nrds_url, nrds_token, nrds_config):
        """
        Downloads new config to whatever is declared as path

        @todo Validate config before saving
        """
        get_args = {
            'configname': nrds_config,
            'cmd': 'getconfig',
            'os': 'NCPA',
            'token': nrds_token
        }

        nrds_response = utils.send_request(nrds_url, **get_args)

        if nrds_response:
            try:
                with open(self.config.file_path, 'wb') as new_config:
                    new_config.write(nrds_response)
            except IOError:
                logging.error(u'Could not rewrite the config. Permissions my be wrong.')
            else:
                logging.info(u'Successfully updated NRDS config.')

    @staticmethod
    def config_update_is_required(nrds_url, nrds_token, nrds_config, nrds_config_version):
        """
        Returns true or false based on value in the config_version
        variable in the config

        @todo Log results if we do not have this config
        """
        get_args = {
            'token': nrds_token,
            'cmd': 'updatenrds',
            'os': 'NCPA',
            'configname': nrds_config,
            'version': nrds_config_version
        }

        logging.debug('Connecting to NRDS server (%s)...', nrds_url)

        url_request = utils.send_request(nrds_url, **get_args)

        response_xml = ET.fromstring(url_request)
        status_xml = response_xml.findall('./status')

        if not status_xml:
            logging.warning("NRDS server did not respond with a status, skipping.")
            return False

        status = status_xml[0].text
        if status == "0":
            return False
        elif status == "1":
            return True
        else:
            logging.warning("Server does not have a record for %s config.", nrds_config)
            return False

    @staticmethod
    def get_os():
        plat = sys.platform

        if plat == u'darwin' or plat == u'mac':
            nrds_os = u'Darwin'
        elif u'linux' in plat:
            nrds_os = u'Linux'
        elif u'aix' in plat:
            nrds_os = u'AIX'
        elif u'sun' in plat:
            nrds_os = u'SunOS'
        elif u'win' in plat:
            nrds_os = u'Windows'
        else:
            nrds_os = u'Generic'
        return nrds_os

    def list_missing_plugins(self, *args, **kwargs):
        installed_plugins = self.get_installed_plugins()
        required_plugins = self.get_required_plugins()
        return required_plugins - installed_plugins

    def get_required_plugins(self, *args, **kwargs):
        passive_checks = self.config.items(u'passive checks')
        filtered = [x[1] for x in passive_checks if u'|' in x[0] and u'plugin/' in x[1]]
        PLUGIN_NAME = re.compile(ur'plugin/([^/]+).*')
        return frozenset([PLUGIN_NAME.search(x).group(1) for x in filtered])

    def get_installed_plugins(self, *args, **kwargs):
        logging.warning(self.config.get(u'plugin directives', u'plugin_path'))
        return frozenset(
            [x for x in os.listdir(self.config.get(u'plugin directives', u'plugin_path')) if not x.startswith(u'.')])
