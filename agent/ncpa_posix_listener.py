#!/usr/bin/env python

import logging
import os
import ncpadaemon
import listener.server
import filename
import listener.certificate
import werkzeug.serving
import ConfigParser
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from gevent.pool import Pool
import listener.psapi
# All of the includes below are dummy includes so that cx_Freeze catches them
import jinja2.ext
from gevent import monkey

monkey.patch_all()


class Listener(ncpadaemon.Daemon):
    default_conf = os.path.abspath(os.path.join(filename.get_dirname_file(), 'etc', 'ncpa.cfg'))
    section = 'listener'

    def setup_root_node(self):
        listener.psapi.init_root()

    def run(self):
        try:
            address = self.config_parser.get('listener', 'ip')
            port = self.config_parser.getint('listener', 'port')
            listener.server.listener.config['iconfig'] = self.config_parser

            user_cert = self.config_parser.get('listener', 'certificate')

            if user_cert == 'adhoc':
                basepath = filename.get_dirname_file()
                cert, key = listener.certificate.create_self_signed_cert(basepath, 'ncpa.crt', 'ncpa.key')
            else:
                cert, key = user_cert.split(',')
            ssl_context = {'certfile': cert, 'keyfile': key}

            self.setup_root_node()

            listener.server.listener.secret_key = os.urandom(24)
            http_server = WSGIServer(listener=(address, port),
                                     application=listener.server.listener,
                                     handler_class=WebSocketHandler,
                                     spawn=Pool(100),
                                     **ssl_context)
            http_server.serve_forever()
        except Exception, e:
            logging.exception(e)

if __name__ == u'__main__':
    Listener().main()
