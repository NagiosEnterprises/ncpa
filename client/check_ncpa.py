#!/usr/bin/env python
"""
SYNOPSIS


"""
import sys
import optparse
import traceback

try:
    import json
except ImportError:
    import simplejson as json

# Python2/3 Compatibility imports
try:
    import urllib.request
    import urllib.parse
    import urllib.error
except ImportError:
    import urllib

try:
    urlencode = urllib.parse.urlencode
except AttributeError:
    urlencode = urllib.urlencode
try:
    urlretrieve = urllib.request.urlretrieve
except AttributeError:
    urlretrieve = urllib.urlretrieve

try:
    urlquote = urllib.parse.quote
except AttributeError:
    urlquote = urllib.quote

import shlex
import re
import signal

__VERSION__ = '0.3.5'

def pretty(d, indent=0, indenter=' ' * 4):
    info_str = ''
    for key, value in list(d.items()):
        info_str += indenter * indent + str(key)
        if isinstance(value, dict):
            info_str += '/\n'
            info_str += pretty(value, indent + 1, indenter)
        else:
            info_str += ': ' + str(value) + '\n'
    return info_str


def parse_args():
    version = 'check_ncpa.py, Version %s' % __VERSION__

    parser = optparse.OptionParser()
    parser.add_option("-H", "--hostname", help="The hostname to be connected to.")
    parser.add_option("-M", "--metric", default='',
                      help="The metric to check, this is defined on client "
                           "system. This would also be the plugin name in the "
                           "plugins directory. Do not attach arguments to it, "
                           "use the -a directive for that. DO NOT INCLUDE the api/ "
                           "instruction.")
    parser.add_option("-P", "--port", default=5693, type="int",
                      help="Port to use to connect to the client.")
    parser.add_option("-w", "--warning", default=None, type="str",
                      help="Warning value to be passed for the check.")
    parser.add_option("-c", "--critical", default=None, type="str",
                      help="Critical value to be passed for the check.")
    parser.add_option("-u", "--unit", default=None,
                      help="The unit prefix (M, G, T)")
    parser.add_option("-n", "--units", default=None,
                      help="What should be used in place of the default unit. As in, instead of 'b' as a unit, it will "
                      "use this.")
    parser.add_option("-a", "--arguments", default=None,
                      help="Arguments for the plugin to be run. Not necessary "
                           "unless you're running a custom plugin. Given in the same "
                           "as you would call from the command line. Example: -a '-w 10 -c 20 -f /usr/local'")
    parser.add_option("-t", "--token", default=None,
                      help="The token for connecting.")
    parser.add_option("-T", "--timeout", default=15, type="int",
                      help="Enforced timeout, will terminate plugins after "
                           "this amount of seconds. [%default]")
    parser.add_option("-d", "--delta", action='store_true',
                      help="Signals that this check is a delta check and a "
                           "local state will kept.")
    parser.add_option("-l", "--list", action='store_true',
                      help="List all values under a given node. Do not perform "
                           "a check.")
    parser.add_option("-v", "--verbose", action='store_true',
                      help='Print more verbose error messages.')
    parser.add_option("-s", "--super-verbose", action='store_true',
                      help='Print LOTS of error messages.')
    parser.add_option("-V", "--version", action='store_true',
                      help='Print version number of plugin.')
    parser.add_option("-q", "--queryargs", default=None,
                      help='Extra query arguments to pass in the NCPA URL.')
    options, _ = parser.parse_args()

    if options.version:
        print(version)
        sys.exit(0)

    if options.arguments and options.metric and not 'agent/plugin' in options.metric:
        parser.print_help()
        parser.error('You cannot specify arguments and try to run a plugin.')

    if not options.hostname:
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


# ~ The following are all helper functions. I would normally split these out into
#~ a new module but this needs to be portable.


def get_url_from_options(options):
    host_part = get_host_part_from_options(options)
    arguments = get_arguments_from_options(options)

    return '%s?%s' % (host_part, arguments)


def get_host_part_from_options(options):
    """Gets the address that will be queries for the JSON.

    """
    hostname = options.hostname
    port = options.port

    if not options.metric is None:
        metric = options.metric
    else:
        metric = ''

    arguments = get_check_arguments_from_options(options)
    if not metric and not arguments:
        api_address = 'https://%s:%d/api' % (hostname, port)
    else:
        api_address = 'https://%s:%d/api/%s/%s' % (hostname, port, metric,
                                                   arguments)

    return api_address


def get_check_arguments_from_options(options):
    """Gets the escaped URL for plugin arguments to be added
    to the end of the host URL. This is different from the get_arguments_from_options
    in that this is meant for the syntax when the user is calling a check, whereas the below
    is when GET arguments need to be added.

    """
    arguments = options.arguments
    if arguments is None:
        return ''
    else:
        arguments = '/'.join([urlquote(x, safe='') for x in shlex.split(arguments)])
        return arguments


def get_arguments_from_options(options, **kwargs):
    """Returns the http query arguments. If there is a list variable specified,
    it will return the arguments necessary to query for a list.

    """

    # Note that the distinction between units/unit is a bit confusing. According to the API, the units the is
    # the unit prefix, like K, M or G. Unit is the unit that will be ascribed like B, b, bytes, etc. We have them
    # flip-flopped here and cannot change them due to API versions.
    arguments = {'token': options.token,
                 'units': options.unit}
    
    if not options.list:
        arguments['warning'] = options.warning
        arguments['critical'] = options.critical
        arguments['delta'] = options.delta
        arguments['check'] = 1
        arguments['unit'] = options.units

    if options.queryargs:
        for argument in options.queryargs.split(','):
            key, value = argument.split('=')
            arguments[key] = value

    #~ Encode the items in the dictionary that are not None
    return urlencode(dict((k, v) for k, v in list(arguments.items()) if v))


def get_json(options):
    """Get the page given by the options. This will call down the url and
    encode its finding into a Python object (from JSON).

    """
    url = get_url_from_options(options)

    if options.verbose:
        print('Connecting to: ' + url)

    try:
        filename, _ = urlretrieve(url)
        f = open(filename)
    except IOError:
        url = get_url_from_options(options)
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


def timeout_handler(threshold):
    def wrapped(signum, frames):
        stdout = "UNKNOWN: Execution exceeded timeout threshold of %ds" % threshold
        print stdout
        sys.exit(3)
    return wrapped


def main():
    options = parse_args()

    # We need to ensure that we will only execute for a certain amount of
    # seconds.
    signal.signal(signal.SIGALRM, timeout_handler(options.timeout))
    signal.alarm(options.timeout)

    try:

        if options.version:
            stdout = 'The version of this plugin is %s' % __VERSION__
            return stdout, 0

        info_json = get_json(options)
        if options.list:
            return show_list(info_json)
        else:
            return run_check(info_json)
    except Exception, e:
        if options.super_verbose:
            return 'The stack trace:' + traceback.format_exc(), 3
        elif options.verbose:
            return 'An error occurred:' + str(e), 3
        else:
            return 'UNKNOWN: Error occurred while running the plugin. Use the verbose flag for more details.', 3


if __name__ == "__main__":
    stdout, returncode = main()
    print(stdout)
    sys.exit(returncode)
