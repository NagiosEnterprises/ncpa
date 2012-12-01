#!/usr/bin/env python
"""
SYNOPSIS

    
"""
import socket
import sys
import optparse
import json

def parse_args():
    parser = optparse.OptionParser()
    parser.add_option(  "-H","--hostname",
                        help="The hostname to be connected to." )
    parser.add_option(  "-M","--metric",
                        help="The metric to check, this is defined on client system.")
    parser.add_option(  "-P","--port",
                        default=9990,
                        type="int",
                        help="Port to use to connect to the client.")
    parser.add_option(  "-w","--warning",
                        default=None,
                        type="str",
                        help="Warning value to be passed for the check.")
    parser.add_option(  "-c","--critical",
                        default=None,
                        type="str",
                        help="Critical value to be passed for the check.")
    parser.add_option(  "-s","--spec",
                        default="",
                        type="str")
    options, args = parser.parse_args()
    
    if not options.hostname:
        parser.print_help()
        parser.error("Hostname is required for use.")
    if not options.metric:
        parser.print_help()
        parser.error("Metric is required.")
    
    return options

def query_server(host, metric, port, warning, critical, spec=''):
    data_string = json.dumps({  'metric'    : metric,
                                'warning'   : warning,
                                'critical'  : critical,
                                'spec'      : spec })
    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connect to server and send data
        sock.connect((host, port))
        sock.sendall(data_string + "\n")
        # Receive data from the server and shut down
        received = sock.recv(1024)
    finally:
        sock.close()
    return json.loads(received)

if __name__ == "__main__":
    options = parse_args()
    host = getattr(options, 'hostname')
    port = getattr(options, 'port')
    metric = getattr(options, 'metric')
    warning = getattr(options, 'warning')
    critical = getattr(options, 'critical')
    spec = getattr(options, 'spec')
    received = query_server(host, metric, port, warning, critical, spec)
    print received['stdout']
    sys.exit(received['returncode'])
    #~ parse_result(recieved, options)
