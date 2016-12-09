#!/usr/bin/env python

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
            address = self.config_parser.get('listener', 'ip')
            port = self.config_parser.getint('listener', 'port')
            listener.server.listener.config['iconfig'] = self.config_parser

            user_cert = self.config_parser.get('listener', 'certificate')

            ssl_str_version = self.config_parser.get('listener', 'ssl_version')
            try:
                ssl_version = getattr(ssl, 'PROTOCOL_' + ssl_str_version)
            except:
                ssl_version = getattr(ssl, 'PROTOCOL_TLSv1')
                ssl_str_version = 'TLSv1'
            logging.info('Using SSL version %s', ssl_str_version)

            if user_cert == 'adhoc':
                basepath = filename.get_dirname_file()
                cert, key = listener.certificate.create_self_signed_cert(basepath, 'ncpa.crt', 'ncpa.key')
            else:
                cert, key = user_cert.split(',')

            ssl_context = {
                'certfile': cert,
                'keyfile': key,
                'ssl_version': ssl_version
            }

            listener.server.listener.secret_key = os.urandom(24)
            http_server = WSGIServer(listener=(address, port),
                                     application=listener.server.listener,
                                     handler_class=WebSocketHandler,
                                     spawn=Pool(200),
                                     **ssl_context)
            http_server.serve_forever()
        except Exception, e:
            logging.exception(e)

if __name__ == u'__main__':
    Listener().main()
