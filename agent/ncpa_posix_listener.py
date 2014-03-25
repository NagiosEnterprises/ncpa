#!/usr/bin/env python

import logging
import os
import ncpadaemon
import listener.server
import filename
import werkzeug.serving
import configparser

# All of the includes below are dummy includes so that cx_Freeze catches them
import jinja2.ext

class Listener(ncpadaemon.Daemon):
    default_conf = os.path.abspath(os.path.join(filename.get_dirname_file(), 'etc', 'ncpa.cfg'))
    section = 'listener'
    
    def run(self):
        address = self.config_parser.get('listener', 'ip')
        port = int(self.config_parser.get('listener', 'port'))
        certificate = self.config_parser.get('listener', 'certificate')

        if certificate == 'adhoc':
            key_path = os.path.join(filename.get_dirname_file(), 'var', 'adhoc')
            ssl_context = werkzeug.serving.make_ssl_devcert(key_path, host='localhost')
        else:
            ssl_context = certificate.split(',')

        try:
            logging.info('Starting server...')
            listener.server.listener.config_filename = 'etc/ncpa.cfg'
            listener.server.listener.config['iconfig'] = self.config_parser
            listener.server.listener.secret_key = os.urandom(24)
            try:
                listener.server.listener.run(address, port, ssl_context=ssl_context)
            except Exception as e:
                logging.exception(e)
                listener.server.listener.run(address, port)
        except Exception as e:
            logging.exception(e)

if __name__ == '__main__':
    Listener().main()
