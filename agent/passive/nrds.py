import sys
import xml.etree.ElementTree as ET
import passive.nagioshandler
import passive.utils
import tempfile
import re
from ncpa import passive_logger as logging
import os
import configparser as cp


class Handler(passive.nagioshandler.NagiosHandler):
    """
    Class for handling the passive NRDS component.
    """

    def __init__(self, config):
        super(Handler, self).__init__(config)

    def run(self, *args, **kwargs):
        logging.debug('Establishing passive handler: NRDS')

        # The NRDS section does not exist right now..
        # return
        
        try:
            nrds_url = self.config.get('nrds', 'url')
            nrds_config = self.config.get('nrds', 'config_name')
            nrds_config_version = self.config.get('nrds', 'config_version')
            nrds_token = self.config.get('nrds', 'token')
        except (cp.NoOptionError, cp.NoSectionError) as exc:
            logging.error("Encountered error while getting NRDS config values: %r", exc)

        # logging.info('url: %s, config_name: %s, config_version: %s, token: %s', nrds_url, nrds_config, nrds_config_version, nrds_token)

        # Make sure valid input was stated in the config, if not, error out and log it.
        for directive in [nrds_url, nrds_config, nrds_config_version, nrds_token]:
            if directive is None:
                logging.error("Cannot start NRDS transaction: %r is invalid or missing.", directive)
                return

        # Check to see if an update is required.
        if self.config_update_is_required(nrds_url, nrds_token, nrds_config, nrds_config_version):
            logging.debug('Updating my NRDS config...')
            self.update_config(nrds_url, nrds_token, nrds_config)

            # new_config_version = self.update_config(nrds_url, nrds_token, nrds_config)

            # if new_config_version > nrds_config_version:
            #     logging.debug('Updating config version: %s', new_config_version)
            #     self.config.set('nrds', 'config_version', new_config_version)

            #     # Write change to main config
            #     with open('/usr/local/ncpa/etc/nrds.cfg', 'w') as configfile:
            #         self.config.write(configfile)
            #         logging.debug('Changes written to nrds.cfg, please restart the service for changes to take effect.')

        # Then install any necessary plugins if need be.
        # needed_plugins = self.list_missing_plugins()
        # logging.debug('Needed plugins: %s', needed_plugins)

        # if needed_plugins:
        #     logging.debug('We need some plugins. Getting them...')
        #     for plugin in needed_plugins:
        #         self.get_plugin(plugin)

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
        url_request = passive.utils.send_request(nrds_url, **getargs)
        plugin_abs_path = os.path.join(plugin_path, plugin)

        if plugin_abs_path != os.path.abspath(plugin_abs_path):
            raise ValueError("Plugin path (%s) is not absolute, I will not continue safely.", plugin_abs_path)

        logging.debug("Downloading plugin to location: %s", plugin_abs_path)

        try:
            with open(plugin_abs_path, 'w') as plugin_file:
                plugin_file.write(url_request)
                logging.info("Successfully downloaded plugin: %s", plugin)
                if os.name != 'nt':
                    os.chmod(plugin_abs_path, 775)
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
            'token': nrds_token,
            'connection_timeout': 10
        }

        try:
            # Request the config from the server
            nrds_response = passive.utils.send_request(nrds_url, **get_args)
            nrds_res_decoded = '[nrds]\n'
            nrds_res_decoded += nrds_response.decode('utf-8')
            logging.debug('nrds_response decoded: \n%s', nrds_res_decoded)

            # Try to parse the config downloaded from the server
            test_config = cp.ConfigParser()
            test_config.read_string(nrds_res_decoded)
            logging.debug('temp config: %s', test_config.sections())

            if not test_config.sections():
                raise Exception('Config contained no NCPA directives, not writing.')

            new_config_version = test_config.get('nrds', 'CONFIG_VERSION')
            new_version_stripped = new_config_version.replace('"', '')
            logging.debug('new config file version: %s', new_version_stripped)

            if 'passive checks' in test_config:
                section_data = dict(test_config.items('passive checks'))
                logging.debug('passive checks section data: %s', section_data)
                
                # Create a new parser for the output
                new_config = cp.ConfigParser()
                new_config['passive checks'] = section_data
                logging.debug('passive checks: %s', new_config.sections())

                # Write to a new file
                try:
                    with open('/usr/local/ncpa/etc/ncpa.cfg.d/nrds.cfg', 'w') as new_file:
                        new_file.write(new_config)
                        logging.debug('config file written')
                except Exception as exc:
                    logging.error('Could not rewrite the config: %r', exc)
                    return False 

            # if valid_config:
            #     logging.debug('valid configuration detected')
            #     # Write new config to file
            #     if  nrds_res_decoded:
            #         try:
            #             with open('/usr/local/ncpa/etc/ncpa.cfg.d/nrds.cfg', 'w') as new_config_file:
            #                 new_config_file.write(nrds_res_decoded)
            #         except Exception as exc:
            #             logging.error('Could not rewrite the config: %r', exc)
            #             return False
            #         else:
            #             
            logging.info('Successfully updated NRDS config.')

            return True

        except Exception as exc:
            logging.error("NRDS config received from the server contained errors: %r", exc)
            return False

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
            'version': nrds_config_version,
            'connection_timeout': 10
        }

        logging.debug('Connecting to NRDS server (%s)...', nrds_url)

        url_request = passive.utils.send_request(nrds_url, **get_args)

        response_xml = ET.fromstring(url_request)
        status_xml = response_xml.findall('./status')

        # Debug XML
        # Add indentation to the tree (Python 3.9+)
        # ET.indent(response_xml, space="  ", level=0)
        # Log the formatted tree
        # logging.debug('response xml: \n %s', ET.tostring(response_xml, encoding='unicode'))

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

        logging.debug('installed plugins: %s', installed_plugins)
        logging.debug('required plugins: %s', required_plugins)

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
        logging.debug('plugin path: %s', plugin_path)
        plugins = set()

        try:
            for plugin in os.listdir(plugin_path):
                if not plugin.startswith('.'):
                    plugins.add(plugin)
        except Exception as exc:
            logging.error("Encountered exception while trying to read plugin directory: %r", exc)

        return plugins

