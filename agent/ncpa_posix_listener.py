#!/usr/bin/env python

import logging
import os
import ncpadaemon
import listener.server
import filename
import listener.certificate
import werkzeug.serving
import ConfigParser
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

# All of the includes below are dummy includes so that cx_Freeze catches them
import jinja2.ext

class Listener(ncpadaemon.Daemon):
    default_conf = os.path.abspath(os.path.join(filename.get_dirname_file(), 'etc', 'ncpa.cfg'))
    section = u'listener'
    
    def run(self):
        address = self.config_parser.get('listener', 'ip')
        port = int(self.config_parser.get('listener', 'port'))
        user_cert = self.config_parser.get('listener', 'certificate')

        if user_cert == 'adhoc':
            basepath = filename.get_dirname_file()
            cert, key = listener.certificate.create_self_signed_cert(basepath, 'ncpa.crt', 'ncpa.key')
        else:
            cert, key = user_cert.split(',')
        ssl_context = {'certfile': cert, 'keyfile': key}

        try:
            logging.info('Starting server...')
            listener.server.listener.config_filename = 'etc/ncpa.cfg'
            listener.server.listener.config['iconfig'] = self.config_parser
            listener.server.listener.secret_key = os.urandom(24)
            try:
                http_server = HTTPServer(WSGIContainer(listener.server.listener),
                                         ssl_options=ssl_context)
                http_server.listen(port)
                IOLoop.instance().start()
            except Exception, e:
                logging.exception(e)
        except Exception, e:
            logging.exception(e)

if __name__ == u'__main__':
    Listener().main()
