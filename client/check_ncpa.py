#!/usr/bin/env python
"""
SYNOPSIS


"""
import sys
import optparse

try:
    import json
except ImportError:
    import simplejson as json

try:
    import urllib.request, urllib.parse, urllib.error
except ImportError:
    import urllib
import shlex
import re

__VERSION__ = 0.2


def pretty(d, indent=0, indenter=' '*4):
    info_str = ''
    for key, value in list(d.items()):
        info_str += indenter * indent + str(key)
        if isinstance(value, dict):
            info_str += '/\n'
            info_str += pretty(value, indent+1, indenter)
        else:
            info_str += ': ' + str(value) + '\n'
    return info_str


def parse_args():
    parser = optparse.OptionParser()
    parser.add_option("-H", "--hostname", help="The hostname to be connected to.")
    parser.add_option("-M", "--metric", default='',
                      help="The metric to check, this is defined on client "
                           "system. This would also be the plugin name in the "
                           "plugins directory. Do not attach arguments to it, "
                           "use the -a directive for that.")
    parser.add_option("-P", "--port", default=5693, type="int",
                      help="Port to use to connect to the client.")
    parser.add_option("-w", "--warning", default=None, type="str",
                      help="Warning value to be passed for the check.")
    parser.add_option("-c", "--critical", default=None, type="str",
                      help="Critical value to be passed for the check.")
    parser.add_option("-u", "--unit", default=None,
                      help="The unit prefix (M, G, T)")
    parser.add_option("-a", "--arguments", default=None,
                      help="Arguments for the plugin to be run. Not necessary "
                           "unless you're running a custom plugin.")
    parser.add_option("-t", "--token", default=None,
                      help="The token for connecting.")
    parser.add_option("-d", "--delta", action='store_true',
                      help="Signals that this check is a delta check and a "
                           "local state will kept.")
    parser.add_option("-l", "--list", action='store_true',
                      help="List all values under a given node. Do not perform "
                           "a check.")
    parser.add_option("-v", "--verbose", action='store_true',
                      help='Print more verbose error messages.')
    parser.add_option("-V", "--version", action='store_true',
                      help='Print version number of plugin.')
    options, _ = parser.parse_args()

    if options.version:
        pass # we just want to return

    elif not options.hostname:
        parser.print_help()
        parser.error("Hostname is required for use.")

    elif not options.token:
        parser.print_help()
        parser.error("A token is most definitely required.")

    elif not options.metric and not options.list:
        parser.print_help()
        parser.error('No metric given, if you want to list all possible items '
                     'use --list.')

    options.metric = re.sub(r'^/?(api/)?', '', options.metric)

    return options

#~ The following are all helper functions. I would normally split these out into
#~ a new module but this needs to be portable.


def get_url_from_options(options, **kwargs):
    host_part = get_host_part_from_options(options, **kwargs)
    arguments = get_arguments_from_options(options, **kwargs)

    return '%s?%s' % (host_part, arguments)


def get_host_part_from_options(options, use_https=True, **kwargs):
    """Gets the address that will be queries for the JSON.

    """
    if use_https:
        protocol = 'https'
    else:
        protocol = 'http'

    hostname = options.hostname
    port = options.port

    if not options.metric is None:
        metric = options.metric
    else:
        metric = ''

    if options.arguments:
        arguments = '/' + '/'.join([x for x in shlex.split(options.arguments)])
    else:
        arguments = ''

    return '%s://%s:%d/api/%s%s' % (protocol, hostname, port, metric, arguments)


def get_arguments_from_options(options, **kwargs):
    """Returns the http query arguments. If there is a list variable specified,
    it will return the arguments necessary to query for a list.

    """
    arguments = {'token': options.token,
                 'unit': options.unit}
    if not options.list:
        arguments['warning'] = options.warning
        arguments['critical'] = options.critical
        arguments['delta'] = options.delta
        arguments['check'] = 1

    try:
        urlencode = urllib.parse.urlencode
    except AttributeError:
        urlencode = urllib.urlencode

    #~ Encode the items in the dictionary that are not None
    return urlencode(dict((k, v) for k, v in list(arguments.items()) if v))

#~ The following function simply call the helper functions.


def get_json(options):
    """Get the page given by the options. This will call down the url and
    encode its finding into a Python object (from JSON). If it fails to pull
    the page down using HTTPS, it will attempt HTTP.

    """
    url = get_url_from_options(options, verbose=options.verbose)

    if options.verbose:
        print('Connecting to: ' + url)

    # Add Python2 vs Python3 support
    try:
        urlretrieve = urllib.request.urlretrieve
    except AttributeError:
        urlretrieve = urllib.urlretrieve

    try:
        filename, _ = urlretrieve(url)
        f = open(filename)
    except IOError:
        url = get_url_from_options(options, use_https=False)
        filename, _ = urlretrieve(url)
        f = open(filename)

    if options.verbose:
        print('File returned contained:\n' + ''.join(f.readlines()))
        f.seek(0)

    return json.load(f)['value']


def run_check(info_json):
    """Run a check against the remote host.

    """
    return info_json['stdout'], info_json['returncode']


def show_list(info_json):
    """Show the list of available options.

    """
    return pretty(info_json), 0


def main():
    try:
        options = parse_args()

        if options.version:
            global __VERSION__
            stdout = 'The version of this plugin is %.1f' % __VERSION__
            return stdout, 0

        info_json = get_json(options)
        if options.list:
            return show_list(info_json)
        else:
            return run_check(info_json)
    except Exception as e:
        if options.verbose:
            return 'An error occurred:' + str(e), 3
        else:
            return 'UNKNOWN: Error occurred while running the plugin. Use the verbose flag for more details.', 3

if __name__ == "__main__":
    stdout, returncode = main()
    print(stdout)
    sys.exit(returncode)
