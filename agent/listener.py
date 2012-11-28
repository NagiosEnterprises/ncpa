#!/usr/bin/env python

import SocketServer
import processor
import json

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
        #~ print "{} wrote:".format(self.client_address[0])
        jsondata = json.loads(self.data)
        returnstr = processor.check_metric(jsondata)
        # just send back the same data, but upper-cased
        self.request.sendall(returnstr)

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 9990

    # Create the server, binding to localhost on port 9994
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        server.serve_forever()
    except:
        server.shutdown()
    finally:
        server.shutdown()
