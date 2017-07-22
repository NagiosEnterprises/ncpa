from __future__ import with_statement
import sys
import xml.etree.ElementTree as ET
import listener.server
import nagioshandler
import utils
import tempfile
import re
import logging
import os
import ConfigParser


class Handler(nagioshandler.NagiosHandler):
    """
    Class for handling the passive NRDS component.
    """

    def __init__(self, config):
        super(Handler, self).__init__(config)

    def run(self, *args, **kwargs):
        logging.debug('Establishing passive handler: NRDS')

        # The NRDS section does not exist right now..
        return
        
        try:
            nrds_url = self.config.get('nrds', 'url')
            nrds_config = self.config.get('nrds', 'config_name')
            nrds_config_version = self.config.get('nrds', 'config_version')
            nrds_token = self.config.get('nrds', 'token')
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError) as exc:
            logging.error("Encountered error while getting NRDS config values: %r", exc)

        # Make sure valid input was stated in the config, if not, error out and log it.
        for directive in [nrds_url, nrds_config, nrds_config_version, nrds_token]:
            if directive is None:
                logging.error("Cannot start NRDS transaction: %r is invalid or missing.", directive)
                return

        # Check to see if an update is required.
        if self.config_update_is_required(nrds_url, nrds_token, nrds_config, nrds_config_version):
            logging.debug('Updating my NRDS config...')
            self.update_config(nrds_url, nrds_token, nrds_config)

        # Then install any necessary plugins if need be.
        needed_plugins = self.list_missing_plugins()
        if needed_plugins:
            logging.debug('We need some plugins. Getting them...')
            for plugin in needed_plugins:
                self.get_plugin(plugin)

        logging.debug('Done with this NRDS iteration.')

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

    def update_config(self, nrds_url, nrds_token, nrds_config):
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

        try:
            with tempfile.TemporaryFile() as temp_config:
                temp_config = tempfile.TemporaryFile()
                temp_config.write(nrds_response)
                temp_config.seek(0)

                test_config = ConfigParser.ConfigParser()
                test_config.readfp(temp_config)

                if not test_config.sections():
                    raise Exception('Config contained no NCPA directives, not writing.')
        except Exception as exc:
            logging.error("NRDS config received from the server contained errors: %r", exc)
            return False

        if nrds_response:
            try:
                with open(self.config.file_path, 'wb') as new_config:
                    new_config.write(nrds_response)
            except Exception as exc:
                logging.error('Could not rewrite the config: %r', exc)
                return False
            else:
                logging.info('Successfully updated NRDS config.')
        return True


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
        """
        Gets the current operation system we are working on. Used for determining which architecture/build of the
        plugin we wish to retrieve.

        :return: A string representing our OS
        :rtype: str
        """
        plat = sys.platform

        if plat == 'darwin' or plat == 'mac':
            nrds_os = 'Darwin'
        elif 'linux' in plat:
            nrds_os = 'Linux'
        elif 'aix' in plat:
            nrds_os = 'AIX'
        elif 'sun' in plat:
            nrds_os = 'SunOS'
        elif 'win' in plat:
            nrds_os = 'Windows'
        else:
            nrds_os = 'Generic'
        return nrds_os

    def list_missing_plugins(self):
        """
        List the plugins that will need to retrieved from the NRDS server.

        :return: The set containing a list of plugin names
        :rtype: set
        """
        installed_plugins = self.get_installed_plugins()
        required_plugins = self.get_required_plugins()
        return required_plugins - installed_plugins

    def get_required_plugins(self):
        """
        List the plugins that are in the plugins directory

        :return: The set containing a list of plugin names
        :rtype: set
        """
        checks_in_config = self.config.items('passive checks')
        required_plugins = set()

        for target, check in checks_in_config:
            if '|' in target:
                if 'plugin/' in check:
                    plugin_search = re.search(u'plugin/([^/]+).*', check)
                    plugin_name = plugin_search.group(1)
                    required_plugins.add(plugin_name)

        return required_plugins

    def get_installed_plugins(self):
        """
        Return a set containing the plugins that exist in the plugins/ directory.

        :return: Set containing all the plugins that already exist in the plugins/ directory.
        :rtype: set
        """
        logging.debug("Checking for installed plugins.")
        plugin_path = self.config.get('plugin directives', 'plugin_path')
        plugins = set()

        try:
            for plugin in os.listdir(plugin_path):
                if not plugin.startswith('.'):
                    plugins.add(plugin)
        except Exception as exc:
            logging.error("Encountered exception while trying to read plugin directory: %r", exc)

        return plugins

