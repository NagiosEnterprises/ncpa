from __future__ import with_statement
import sys
import abstract
import xml.etree.ElementTree as ET
from passive.nagioshandler import NagiosHandler
import utils
import re
import logging
import os


class Handler(NagiosHandler):
    u"""
    api for nrds config management
    """

    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)

    def get_nrds_url(self):
        nrds_url = self.config.get('nrds', 'url')
        if nrds_url.endswith('/'):
            return nrds_url
        else:
            return nrds_url + '/'

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

    def get_plugin(self, plugin, *args, **kwargs):
        nrds_url = self.get_nrds_url()
        plugin_path = self.config.get(u'plugin directives', u'plugin_path')
        token = self.config.get(u'nrds', u'token')
        operating_sys = self.get_os()

        getargs = {u'cmd': u'getplugin',
                   u'os': operating_sys,
                   u'token': token,
                   u'plugin':   plugin}

        url_request = utils.send_request(nrds_url, **getargs)
        local_path_location = os.path.join(plugin_path, plugin)

        logging.debug( u"Downloading plugin to location: %s" % unicode(local_path_location))

        try:
            with open(local_path_location, u'w') as plugin_file:
                plugin_file.write(url_request.content)
                os.chmod(local_path_location, 0775)
        except IOError:
            logging.error(u'Could not write the plugin to %s, perhaps permissions went bad.', local_path_location)

    def update_config(self, *args, **kwargs):
        u'''Downloads new config to whatever is declared as path

        @todo Validate config before saving
        '''
        nrds_url = self.get_nrds_url()
        get_args = {u'configname': self.config.get(u'nrds', u'CONFIG_NAME'),
                    u'cmd': u'getconfig',
                    u'os': u'NCPA',
                    u'token': self.config.get(u'nrds', u'token') }


        logging.debug(u'URL I am requesting: %s' % nrds_url)
        url_request = utils.send_request(nrds_url, **get_args)

        if url_request.content != u"":
            try:
                with open(self.config.file_path, u'wb') as config:
                    config.write(url_request.content)
            except IOError:
                logging.error(u'Could not rewrite the config. Permissions my be wrong.')
            else:
                logging.info(u'Successfully updated NRDS config.')



    def config_update_is_required(self, *args, **kwargs):
        u'''Returns true or false based on value in the config_version
        variable in the config

        @todo Log results if we do not have this config
        '''
        get_args = {u'token': self.config.get(u'nrds', u'token'),
                    u'cmd': u'updatenrds',
                    u'os': u'NCPA',
                    u'configname': self.config.get(u'nrds', u'CONFIG_NAME'),
                    u'version': self.config.get(u'nrds', u'CONFIG_VERSION'), }

        logging.debug(u'Connecting to NRDS server...')

        nrdp_url = self.get_nrds_url()
        url_request = utils.send_request(nrdp_url, **get_args)

        response_xml = ET.fromstring(url_request.content)
        status_xml = response_xml.findall(u'./status')

        if status_xml:
            status = status_xml[0].text
        else:
            status = u"0"

        try:
            status = int(status)
        except Exception:
            logging.error(u"Unrecognized value for NRDS update returned. Got %s, excpected integer." % status)
            return False

        logging.debug(u'Value returned for new config: %d' % status)

        if status == 2:
            logging.warning(u"Server does not have a record for %s config." % self.config.get(u'nrds', u'config_name'))
            status = 0

        return bool(status)

    def get_os(self):
        plat = sys.platform

        if plat == u'darwin' or plat == u'mac':
            os = u'Darwin'
        elif u'linux' in plat:
            os = u'Linux'
        elif u'aix' in plat:
            os = u'AIX'
        elif u'sun' in plat:
            os = u'SunOS'
        elif u'win' in plat:
            os = u'Windows'
        else:
            os = u'Generic'
        return os

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
        return frozenset([x for x in os.listdir(self.config.get(u'plugin directives', u'plugin_path')) if not x.startswith(u'.')])
