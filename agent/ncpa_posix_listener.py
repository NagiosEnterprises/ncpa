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
# All of the includes below are dummy includes so that cx_Freeze catches them
import jinja2.ext

class Listener(ncpadaemon.Daemon):
    default_conf = os.path.abspath(os.path.join(filename.get_dirname_file(), 'etc', 'ncpa.cfg'))
    section = u'listener'
    
    def run(self):
        try:
            address = self.config.get('listener', 'ip')
            port = self.config.getint('listener', 'port')
            listener.server.listener.config_file = self.config_filename
            listener.server.listener.config['iconfig'] = self.config

            user_cert = self.config.get('listener', 'certificate')

            if user_cert == 'adhoc':
                basepath = self.get_dirname_file('')
                cert, key = listener.certificate.create_self_signed_cert(basepath, 'ncpa.crt', 'ncpa.key')
            else:
                cert, key = user_cert.split(',')
            ssl_context = {'certfile': cert, 'keyfile': key}

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
