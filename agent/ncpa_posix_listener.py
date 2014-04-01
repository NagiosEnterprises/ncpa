#!/usr/bin/env python3.4

import logging
import os
import ncpadaemon
import listener.server
import filename
import werkzeug.serving
import ConfigParser

# All of the includes below are dummy includes so that cx_Freeze catches them
import jinja2.ext

class Listener(ncpadaemon.Daemon):
    default_conf = os.path.abspath(os.path.join(filename.get_dirname_file(), u'etc', u'ncpa.cfg'))
    section = u'listener'
    
    def run(self):
        address = self.config_parser.get(u'listener', u'ip')
        port = int(self.config_parser.get(u'listener', u'port'))
        certificate = self.config_parser.get(u'listener', u'certificate')

        if certificate == u'adhoc':
            ssl_context = u'adhoc'
        else:
            ssl_context = certificate.split(u',')

        try:
            logging.info(u'Starting server...')
            listener.server.listener.config_filename = u'etc/ncpa.cfg'
            listener.server.listener.config[u'iconfig'] = self.config_parser
            listener.server.listener.secret_key = os.urandom(24)
            try:
                listener.server.listener.run(address, port, ssl_context=ssl_context)
            except Exception, e:
                logging.exception(e)
                listener.server.listener.run(address, port)
        except Exception, e:
            logging.exception(e)

if __name__ == u'__main__':
    Listener().main()
