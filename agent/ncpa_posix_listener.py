#!/usr/bin/env python

import simpledaemon
import logging
import time
import flask
import listener.server

class Listener(simpledaemon.Daemon):
    default_conf = 'etc/ncpa.cfg'
    section = 'listener'
    
    def run(self):
        address = self.config_parser.get('listener', 'ip')
        port = int(self.config_parser.get('listener', 'port'))
        try:
            logging.info('Starting server...')
            listener.server.listener.config['iconfig'] = self.config_parser
            listener.server.listener.run(address, port)
            flask.url_for('static', filename='jquery-1.8.3.min.js')
            flask.url_for('static', filename='jquery-ui.css')
            flask.url_for('static', filename='jquery-ui.js')
        except Exception, e:
            logging.exception(e)

if __name__ == '__main__':
    Listener().main()
