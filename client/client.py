#!/usr/bin/env python
"""
SYNOPSIS

    
"""
import socket
import sys
import optparse
import json
import requests

def parse_args():
    parser = optparse.OptionParser()
    parser.add_option(  "-H","--hostname",
                        help="The hostname to be connected to." )
    parser.add_option(  "-M","--metric",
                        help="The metric to check, this is defined on client system. This would also be the plugin name in the plugins directory. Do not attach arguments to it, use the -a directive for that.")
    parser.add_option(  "-P","--port",
                        default=5691,
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
    parser.add_option(  "-a","--arguments",
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

def query_server(host, *args, **kwargs):
    result = requests.get(host, params=kwargs, verify=False)
    return result.json()

if __name__ == "__main__":
    options = parse_args()
    host = 'http://' + options.hostname + ':' + str(options.port)
    received = query_server(host, **options.__dict__)
    try:
        print received['stdout'],
        sys.exit(received['returncode'])
    except KeyError:
        print 'ERROR:', received['error']
        sys.exit(3)

