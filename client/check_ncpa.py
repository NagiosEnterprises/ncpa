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


def pretty(d, indent=0, indenter='    '):
    for key, value in d.iteritems():
        print indenter * indent + str(key), ':',
        if isinstance(value, dict):
            print ''
            pretty(value, indent+1, indenter)
        else:
            print str(value)


def parse_args():
    parser = optparse.OptionParser()
    parser.add_option("-H", "--hostname", help="The hostname to be connected to.")
    parser.add_option("-M", "--metric", default='',
                      help="The metric to check, this is defined on client system. This would also be the plugin name "
                           "in the plugins directory. Do not attach arguments to it, use the -a directive for that.")
    parser.add_option("-P", "--port", default=5693, type="int",
                      help="Port to use to connect to the client.")
    parser.add_option("-w", "--warning", default=None, type="str",
                      help="Warning value to be passed for the check.")
    parser.add_option("-c", "--critical", default=None, type="str",
                      help="Critical value to be passed for the check.")
    parser.add_option("-u", "--unit", default=None,
                      help="The unit prefix (M, G, T)")
    parser.add_option("-a", "--arguments", default=None,
                      help="Arguments for the plugin to be run. Not necessary unless you're running a custom plugin.")
    parser.add_option("-t", "--token", default=None,
                      help="The token for connecting.")
    parser.add_option("-d", "--delta", action='store_true',
                      help="Signals that this check is a delta check and a local state will kept.")
    parser.add_option("-l", "--list", action='store_true',
                      help="List all values under a given node. Do not perform a check.")
    parser.add_option("-v", "--verbose", action='store_true',
                      help='Print more verbose error messages.')
    input_options, _ = parser.parse_args()
    
    if not input_options.hostname:
        parser.print_help()
        parser.error("Hostname is required for use.")
    
    return input_options


def main(o):
    host = 'https://%s:%d/api/%s?%%s' % (o.hostname, o.port, o.metric)

    if not o.list:
        gets = {'arguments': o.arguments,
                'warning': o.warning,
                'critical': o.critical,
                'unit': o.unit,
                'token': o.token,
                'delta': o.delta,
                'check': 1
                }
    else:
        gets = {'token': o.token,
                'unit': o.unit}

    gets = dict((k, v) for k, v in gets.iteritems() if v is not None)
    query = urllib.urlencode(gets)
    
    url = host % query
    
    try:
        filename, fobject = urllib.urlretrieve(url)
        fileobj = open(filename)
    except:
        if options.verbose:
            'Resorting to http...'
        host = url_tmpl % ('http', options.hostname, options.port, options.metric)
        url = host % query
        filename, fobject = urllib.urlretrieve(url)
        fileobj = open(filename)
    
    try:
        rjson = json.load(fileobj)
    except Exception, e:
        if options.verbose:
            print 'Unable to parse json output'
        stdout, returncode = 'UNKNOWN: %s' % str(e), 3

    if o.list:
        pretty(rjson['value'])
    else:
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
