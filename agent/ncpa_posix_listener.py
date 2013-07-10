#!/usr/bin/env python

import simpledaemon
import logging
import time
import flask
import os
import listener.server

class Listener(simpledaemon.Daemon):
    default_conf = 'etc/ncpa.cfg'
    section = 'listener'
    
    def run(self):
        address = self.config_parser.get('listener', 'ip')
        port = int(self.config_parser.get('listener', 'port'))
        certificate = self.config_parser.get('listener', 'certificate')
        try:
            logging.info('Starting server...')
            listener.server.listener.config['iconfig'] = self.config_parser
            listener.server.listener.secret_key = os.urandom(24)
            listener.server.listener.run(address, port)
        except Exception, e:
            logging.exception(e)

if __name__ == '__main__':
    Listener().main()
