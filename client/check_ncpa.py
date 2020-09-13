#!/usr/bin/env python
"""
SYNOPSIS


"""
import sys
import optparse
import traceback
import ssl

# Python 2/3 Compatibility imports

try:
    import json
except ImportError:
    import simplejson as json

try:
    import urllib.request
    import urllib.parse
    import urllib.error
except ImportError:
    import urllib2
    import urllib

try:
    urlencode = urllib.parse.urlencode
except AttributeError:
    urlencode = urllib.urlencode

try:
    urlopen = urllib.request.urlopen
except AttributeError:
    urlopen = urllib2.urlopen

try:
    urlquote = urllib.parse.quote
except AttributeError:
    urlquote = urllib.quote

try:
    urlerror = urllib.error.URLError
except AttributeError:
    urlerror = urllib2.URLError

try:
    httperror = urllib.error.HTTPError
except AttributeError:
    httperror = urllib2.HTTPError

import shlex
import re
import signal

__VERSION__ = '1.2.4'


class ConnectionError(Exception):
    error_output_prefix = "UNKNOWN: An error occured connecting to API. "
    pass


class URLError(ConnectionError):
    def __init__(self, error_message):
        self.error_message = ConnectionError.error_output_prefix + "(Connection error: '" + error_message + "')"


class HTTPError(ConnectionError):
    def __init__(self, error_message):
        self.error_message = ConnectionError.error_output_prefix + "(HTTP error: '" + error_message + "')"


def parse_args():
    version = 'check_ncpa.py, Version %s' % __VERSION__

    parser = optparse.OptionParser(add_help_option=False)
    general = optparse.OptionGroup(parser, "General Options")
    general.add_option("-h", "--help", action='help',
                       help='show this help message and exit')
    general.add_option("-H", "--hostname", help="The hostname to be connected to.")
    general.add_option("-M", "--metric", default='',
                       help="The metric to check, this is defined on client "
                            "system. This would also be the plugin name in the "
                            "plugins directory. Do not attach arguments to it, "
                            "use the -a directive for that. DO NOT INCLUDE the api/ "
                            "instruction.")
    general.add_option("-P", "--port", default=5693, type="int",
                       help="Port to use to connect to the client.")
    general.add_option("-w", "--warning", default=None, type="str",
                       help="Warning value to be passed for the check.")
    general.add_option("-c", "--critical", default=None, type="str",
                       help="Critical value to be passed for the check.")
    general.add_option("-u", "--units", default=None,
                       help="The unit prefix (k, Ki, M, Mi, G, Gi, T, Ti) for b and B unit "
                            "types which calculates the value returned.")
    general.add_option("-n", "--unit", default=None,
                       help="Overrides the unit with whatever unit you define. "
                            "Does not perform calculations. This changes the unit of measurement only.")
    general.add_option("-a", "--arguments", default=None,
                       help="Arguments for the plugin to be run. Not necessary "
                            "unless you're running a custom plugin. Given in the same "
                            "as you would call from the command line. Example: -a '-w 10 -c 20 -f /usr/local'")
    general.add_option("-t", "--token", default='',
                       help="The token for connecting.")
    general.add_option("-T", "--timeout", default=60, type="int",
                       help="Enforced timeout, will terminate plugins after "
                            "this amount of seconds. [%default]")
    general.add_option("-d", "--delta", action='store_true',
                       help="Signals that this check is a delta check and a "
                            "local state will kept.")
    general.add_option("-l", "--list", action='store_true',
                       help="List all values under a given node. Do not perform "
                            "a check.")
    general.add_option("-v", "--verbose", action='store_true',
                       help='Print more verbose error messages.')
    general.add_option("-D", "--debug", action='store_true',
                       help='Print LOTS of error messages. Used mostly for debugging.')
    general.add_option("-V", "--version", action='store_true',
                       help='Print version number of plugin.')
    general.add_option("-q", "--queryargs", default=None,
                       help='Extra query arguments to pass in the NCPA URL.')
    general.add_option("-s", "--secure", action='store_true', default=False,
                       help='Require successful certificate verification. Does not work on Python < 2.7.9.')
    parser.add_option_group(general)

    perfdata = optparse.OptionGroup(parser, "Performance Data Options")
    perfdata.add_option("-p", "--performance", action='store_true', default=False,
                        help='Print performance data even when there is none. '
                             'Will print data matching the return code of this script')
    perfdata.add_option("-A", "--perfdata-prefix", action='store', type="string",
                        help='Add a prefix to perfdata labels.')
    perfdata.add_option("-B", "--perfdata-suffix", action='store', type="string",
                        help='Add a suffix to perfdata labels.')
    parser.add_option_group(perfdata)

    output = optparse.OptionGroup(parser, "Output Manipulation Options")
    output.add_option("-L", "--html-single-line", action='store_true', default=False,
                        help='Convert multi line output to single line html output.')
    parser.add_option_group(output)

    options, _ = parser.parse_args()

    if options.version:
        print(version)
        sys.exit(0)

    if options.arguments and options.metric and 'plugin' not in options.metric:
        parser.print_help()
        parser.error('You cannot specify arguments without running a custom plugin.')

    if not options.hostname:
        parser.print_help()
        parser.error("Hostname is required for use.")

    elif not options.metric and not options.list:
        parser.print_help()
        parser.error('No metric given, if you want to list all possible items '
                     'use --list.')

    options.metric = re.sub(r'^/?(api/)?', '', options.metric)

    return options


# The following are all helper functions. I would normally split these out into
# a new module but this needs to be portable.


def get_url_from_options(options):
    host_part = get_host_part_from_options(options)
    arguments = get_arguments_from_options(options)
    return '%s?%s' % (host_part, arguments)


def get_host_part_from_options(options):
    """Gets the address that will be queries for the JSON.

    """
    hostname = options.hostname
    port = options.port

    if options.metric is not None:
        metric = urlquote(options.metric)
    else:
        metric = ''

    arguments = get_check_arguments_from_options(options)
    if not metric and not arguments:
        api_address = 'https://%s:%d/api' % (hostname, port)
    else:
        api_address = 'https://%s:%d/api/%s/%s' % (hostname, port, metric, arguments)

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
        lex = shlex.shlex(arguments)
        lex.whitespace_split = True
        arguments = '/'.join([urlquote(x, safe='') for x in lex])
        return arguments


def get_arguments_from_options(options, **kwargs):
    """Returns the http query arguments. If there is a list variable specified,
    it will return the arguments necessary to query for a list.

    """

    # Note: Changed back to units due to the units being what is passed via the
    # API call which can confuse people if they don't match
    arguments = {'token': options.token,
                 'units': options.units}

    if not options.list:
        arguments['warning'] = options.warning
        arguments['critical'] = options.critical
        arguments['delta'] = options.delta
        arguments['check'] = 1
        arguments['unit'] = options.unit

    args = list((k, v) for k, v in list(arguments.items()) if v is not None)

    # Get the options (comma separated)
    if options.queryargs:
        # for each comma, perform lookahead, split if we aren't inside quotes.
        arguments_list = re.split(''',(?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', options.queryargs)
        for argument in arguments_list:
            key, value = argument.split('=', 1)
            if value is not None:
                args.append((key, value))

    # Encode the items in the dictionary that are not None
    return urlencode(args)


def get_json(options):
    """Get the page given by the options. This will call down the url and
    encode its finding into a Python object (from JSON).

    """

    url = get_url_from_options(options)

    if options.verbose:
        print('Connecting to: ' + url)

    try:

        try:
            ctx = ssl.create_default_context()
            if not options.secure:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            ret = urlopen(url, context=ctx)
        except AttributeError:
            ret = urlopen(url)

    except httperror as e:
        try:
            raise HTTPError('{0} {1}'.format(e.code, e.reason))
        except AttributeError:
            raise HTTPError('{0}'.format(e.code))
    except urlerror as e:
        raise URLError('{0}'.format(e.reason))

    ret = ret.read()

    if options.verbose:
        print('File returned contained:\n' + ret)

    arr = json.loads(ret)

    if options.list:
        return arr

    # Fix for NCPA < 2
    if 'value' in arr:
        arr = arr['value']

        # We need to flip the returncode and stdout
        if isinstance(arr['stdout'], int) and not isinstance(arr['returncode'], int):
            tmp = arr['returncode']
            arr['returncode'] = arr['stdout']
            arr['stdout'] = tmp

    # If we recieve and error, return critical and give out error text
    elif 'error' in arr:
        arr['stdout'] = 'CRITICAL: %s' % arr['error']
        arr['returncode'] = 2

    return arr


def run_check(info_json):
    """Run a check against the remote host.

    """
    if 'stdout' in info_json and 'returncode' in info_json:
        return info_json['stdout'], info_json['returncode']
    elif 'error' in info_json:
        return info_json['error'], 3


def show_list(info_json):
    """Show the list of available options.

    """
    return json.dumps(info_json, indent=4), 0


def split_stdout(stdout):
    """Split stdout to output and perfdata (if available).

    """
    match = re.match(r"^(.*)(\|)(.*)$", stdout)
    if match is not None:
        return match.group(1), list(match.group(3).strip().split(" "))
    else:
        return stdout, None


def add_perfdata_prefix(perfdata, perfdata_prefix):
    """Add the perfdata prefix to perfdata.

    """
    perfdata_list = []
    for ds in perfdata:
        match = re.match(r"^(')(.*)(')(=)(.*)$", ds)
        if match is not None:
            perfdata_list.append("'{0}{1}'={2}".format(perfdata_prefix, match.group(2), match.group(5)))
    return perfdata_list


def add_perfdata_suffix(perfdata, perfdata_suffix):
    """Add the perfdata suffix to perfdata.

    """
    perfdata_list = []
    for ds in perfdata:
        match = re.match(r"^(')(.*)(')(=)(.*)$", ds)
        if match is not None:
            perfdata_list.append("'{0}{1}'={2}".format(match.group(2), perfdata_suffix, match.group(5)))
    return perfdata_list


def timeout_handler(threshold):
    def wrapped(signum, frames):
        stdout = "UNKNOWN: Execution exceeded timeout threshold of %ds" % threshold
        print(stdout)
        sys.exit(3)

    return wrapped


def main():
    options = parse_args()

    # We need to ensure that we will only execute for a certain amount of
    # seconds.
    signal.signal(signal.SIGALRM, timeout_handler(options.timeout))
    signal.alarm(options.timeout)

    try:
        info_json = get_json(options)

        if options.list:
            return show_list(info_json)
        else:
            stdout, returncode = run_check(info_json)

            if options.performance and stdout.find("|") == -1:
                stdout = "{0} | 'status'={1};1;2;;".format(stdout, returncode)

            stdout, perfdata = split_stdout(stdout)

            if perfdata is not None:
                if options.perfdata_prefix is not None:
                    perfdata = add_perfdata_prefix(perfdata, options.perfdata_prefix)
                if options.perfdata_suffix is not None:
                    perfdata = add_perfdata_suffix(perfdata, options.perfdata_suffix)
                stdout = stdout + '| ' + ' '.join(perfdata)

            return stdout, returncode
    except (HTTPError, URLError) as e:
        if options.debug:
            return 'The stack trace:\n' + traceback.format_exc(), 3
        elif options.verbose:
            return 'An error occurred:\n' + str(e.error_message), 3
        else:
            return e.error_message, 3
    except Exception as e:
        if options.debug:
            return 'The stack trace:\n' + traceback.format_exc(), 3
        elif options.verbose:
            return 'An error occurred:\n' + str(e), 3
        else:
            return 'UNKNOWN: Error occurred while running the plugin. Use the verbose flag for more details.', 3


if __name__ == "__main__":
    stdout, returncode = main()
    print(stdout.encode('utf-8', 'replace').decode('utf-8'))
    sys.exit(returncode)
