#!/usr/bin/env python

import logging
import os

import ncpadaemon
import listener.server

try:
    import configparser
except ImportError:
    import configparser as configparser

#DEBUG = True


class Listener(ncpadaemon.Daemon):
    default_conf = os.path.abspath(os.path.join(os.path.dirname(__file__), 'etc', 'ncpa.cfg'))
    section = 'listener'
    
    def run(self):
        address = self.config_parser.get('listener', 'ip')
        port = int(self.config_parser.get('listener', 'port'))
        certificate = self.config_parser.get('listener', 'certificate')
        try:
            logging.info('Starting server...')
            listener.server.listener.config_filename = 'etc/ncpa.cfg'
            listener.server.listener.config['iconfig'] = self.config_parser
            listener.server.listener.secret_key = os.urandom(24)
            try:
                listener.server.listener.run(address, port, ssl_context=self.config_parser.get('listener', 'certificate'))
            except Exception as e:
                logging.exception(e)
                listener.server.listener.run(address, port)
        except Exception as e:
            logging.exception(e)

if __name__ == '__main__':
    Listener().main()
