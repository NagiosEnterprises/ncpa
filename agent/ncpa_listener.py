#!/usr/bin/env python

import warnings
warnings.simplefilter('ignore')

import logging
import os
import ncpadaemon
import listener.server
import filename
import listener.certificate
from gevent.pywsgi import WSGIServer
from gevent.pool import Pool
from geventwebsocket.handler import WebSocketHandler
import listener.psapi
import jinja2.ext  # Here for cx_Freeze import reasons, do not remove it
import sys
import ssl
if 'threading' in sys.modules:
    del sys.modules['threading']
import gevent.builtins
from gevent import monkey
monkey.patch_all(subprocess=True)


class Listener(ncpadaemon.Daemon):
    default_conf = os.path.abspath(os.path.join(filename.get_dirname_file(), 'etc', 'ncpa.cfg'))
    section = 'listener'

    def run(self):

        # Set absolute plugin path
        plugins_abs = os.path.abspath(os.path.join(filename.get_dirname_file(), self.config_parser.get(u'plugin directives', u'plugin_path')))
        self.config_parser.set(u'plugin directives', u'plugin_path', plugins_abs)

        # Check if there is a start delay
        try:
            delay_start = self.config_parser.get('listener', 'delay_start')
            if delay_start:
                logging.info('Delayed start in configuration. Waiting %s seconds to start.', delay_start)
                time.sleep(int(delay_start))
        except Exception:
            pass

        # Handle DB maintenance
        self.db.run_db_maintenance(self.config_parser)

        try:
            try:
                address = self.config_parser.get('listener', 'ip')
            except Exception:
                self.config_parser.set('listener', 'ip', '::')
                address = '::'

            try:
                port = self.config_parser.getint('listener', 'port')
            except Exception:
                self.config_parser.set('listener', 'port', 5693)
                port = 5693

            listener.server.listener.config['iconfig'] = self.config_parser

            user_cert = self.config_parser.get('listener', 'certificate')
            ssl_str_version = self.config_parser.get('listener', 'ssl_version')

            try:
                ssl_str_ciphers = self.config_parser.get('listener', 'ssl_ciphers')
            except Exception:
                ssl_str_ciphers = None

            try:
                ssl_version = getattr(ssl, 'PROTOCOL_' + ssl_str_version)
            except:
                ssl_version = getattr(ssl, 'PROTOCOL_TLSv1')
                ssl_str_version = 'TLSv1'
            logging.info('Using SSL version %s', ssl_str_version)

            if user_cert == 'adhoc':
                basepath = filename.get_dirname_file()
                certpath = os.path.abspath(os.path.join(basepath, 'var'))
                cert, key = listener.certificate.create_self_signed_cert(certpath, 'ncpa.crt', 'ncpa.key')
            else:
                cert, key = user_cert.split(',')

            # Create SSL context that will be passed to the server
            ssl_context = {
                'certfile': cert,
                'keyfile': key,
                'ssl_version': ssl_version
            }

            # Add SSL cipher list if one is given
            if ssl_str_ciphers:
                ssl_context['ciphers'] = ssl_str_ciphers

            # Create connection pool
            try:
                max_connections = self.config_parser.get('listener', 'max_connections')
            except Exception:
                max_connections = 200

            listener.server.listener.secret_key = os.urandom(24)
            http_server = WSGIServer(listener=(address, port),
                                     application=listener.server.listener,
                                     handler_class=WebSocketHandler,
                                     spawn=Pool(max_connections),
                                     **ssl_context)
            http_server.serve_forever()
        except Exception, e:
            logging.exception(e)

if __name__ == u'__main__':
    Listener().main()
