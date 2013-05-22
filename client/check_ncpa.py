#!/usr/bin/env python
"""
SYNOPSIS

    
"""
import sys
import optparse
try:
    import json
except:
    import simplejson as json
import urllib
import tempfile
import time
import os

def parse_args():
    parser = optparse.OptionParser()
    parser.add_option(  "-H","--hostname",
                        help="The hostname to be connected to." )
    parser.add_option(  "-M","--metric",
                        help="The metric to check, this is defined on client system. This would also be the plugin name in the plugins directory. Do not attach arguments to it, use the -a directive for that.")
    parser.add_option(  "-P","--port",
                        default=5693,
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
    parser.add_option(  "-u", "--unit",
                        default=None,
                        help="The unit prefix (M, G, T)")
    parser.add_option(  "-a", "--arguments",
                        default=None,
                        help="Arguments for the plugin to be run. Not necessary unless you're running a custom plugin.")
    parser.add_option(  "-t", "--token",
                        default=None,
                        help="The token for connecting.")
    parser.add_option(  "-d", "--delta",
                        action='store_true',
                        help="Signals that this check is a delta check and a local state will kept.")
    parser.add_option(  "-v", "--verbose",
                        action='store_true',
                        help='Print more verbose error messages.')
    options, args = parser.parse_args()
    
    if not options.hostname:
        parser.print_help()
        parser.error("Hostname is required for use.")
    if not options.metric:
        parser.print_help()
        parser.error("Metric is required.")
    
    return options

def main(options):
    host = 'http://%s:%d/api/%s?%%s' % (options.hostname, options.port, options.metric)
    gets = {    'arguments' : options.arguments,
                'warning'   : options.warning,
                'critical'  : options.critical,
                'unit'      : options.unit,
                'token'     : options.token,
                'delta'     : options.delta,
                'check'     : 1
                }
    gets = dict((k,v) for k,v in gets.iteritems() if v is not None)
    query = urllib.urlencode(gets)
    
    url = host % query
    
    filename, fobject = urllib.urlretrieve(url)
    fileobj = open(filename)
    
    rjson = json.load(fileobj)
    
    if 'error' in rjson:
        stdout, returncode = 'UNKNOWN: %s' % rjson['error'], 3
    else:
        stdout, returncode = rjson['value']['stdout'], rjson['value']['returncode']
    
    print stdout
    sys.exit(returncode)

if __name__ == "__main__":
    options = parse_args()
    
    try:
        main(options)
    except Exception, e:
        if options.verbose:
            print "And error was encountered:"
            print e
            sys.exit(3)
        else:
            print 'UNKNOWN: Error occurred while running the plugin.'
            sys.exit(3)
