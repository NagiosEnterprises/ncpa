#!/usr/bin/env python

import SocketServer
import processor
import json
import ConfigParser
import os
import sys
import logging

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(4096).strip()
        logging.debug('Received incoming connection. Info is: %s', self.data)
        #~ print "{} wrote:".format(self.client_address[0])
        jsondata = json.loads(self.data)
        returnstr = processor.check_metric(jsondata)
        # just send back the same data, but upper-cased
        self.request.sendall(returnstr)

def parse_config():
    """
    Parse the agent.cfg config file, required, listening will not run
    without one.
    """
    global config
    config = ConfigParser.ConfigParser()
    path = os.path.realpath('')
    config.read('agent.cfg')

def setup_logger():
    """
    Setup the logger that will aquiesce through all the rest of the
    ncpa.
    """
    global config
    log_config = dict(config.items('logging', 1))
    log_config['level'] = getattr(logging, log_config['log_level'], logging.INFO)
    del log_config['log_level']
    logging.basicConfig(**log_config)

def main():
    '''
    Kickoff the TCP Server
    '''
    global config
    
    HOST = config.get('listening server', 'ip')
    PORT = int(config.get('listening server', 'port'))
    
    # Create the server, binding to localhost on port 9994
    logging.info('Starting TCP Server on %s:%d', HOST, PORT)
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        server.serve_forever()
    except:
        server.shutdown()
    finally:
        server.shutdown()

if __name__ == "__main__":
    
    parse_config()
    setup_logger()
    try:
        main()
    except IOError as e:
        #~ If every other exeptions falls through, just log it
        logging.error(e)
        print 'Exiting listener due to an unhandled exception.'
        print type(e)
