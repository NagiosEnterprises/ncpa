# -*- coding: utf-8 -*-

import logging
import json
import urllib
import urlparse
import time
import hashlib
import listener.server
import listener.database

# Constants to keep track of the passive check runs 
NEXT_RUN = { }

class NCPACheck(object):
    """
    This class is meant to simplify the creation of other classes that
    simply run a command and return it to Nagios is some format. The
    immediate motivation for this is the difference between NSCA and
    NRDP. They share a lot of functionality that would be otherwise
    duplicated and should not be in the abstract class.

    Convenience class for wrapping up the commands defined in the
    config and setting their host/service to be accessed by their
    child classes and running the results.
    """

    def __init__(self, config, instruction, hostname, servicename, duration):
        logging.debug('Initializing NCPA check with %s', instruction)
        self.config = config
        self.hostname = hostname
        self.servicename = servicename
        self.instruction = instruction
        self.duration = float(duration)

        # Set the next run for this specific check
        key = hashlib.sha256(self.hostname + self.servicename).hexdigest()
        if not key in NEXT_RUN:
            NEXT_RUN[key] = 0

    @staticmethod
    def get_api_url_from_instruction(instruction):
        """
        Method to parse the instruction in the config for running an NCPA check

        :param instruction: The instruction to be parsed
        :type instruction: unicode
        :return: Tuple containing the API URL that will be accessed to retrieve
                 information from the local agent and its args
        :rtype:  tuple
        """
        logging.debug('Getting API url for instruction %s', instruction)

        if '?' in instruction or '&' in instruction:
            api_url, api_args = NCPACheck.parse_api_url_style_instruction(instruction)
            api_args.append(('check', '1'))
        else:
            api_url, api_args = NCPACheck.parse_cmdline_style_instruction(instruction)
            api_args['check'] = '1'

        api_url = NCPACheck.normalize_api_url(api_url)

        logging.debug('Determined instruction to be: %s', instruction)
        return api_url, api_args

    def run(self, default_duration=300):
        """
        The primary method for running an NCPA check. Once the method has been
        instantiated this is the only function you should run.

        :return: A tuple containing the stdout and returncode of the NCPA check
        :rtype: tuple
        :raise: Will raise ValueError when either the stdout or returncode are
                not a string
        :raises: ValueError
        """
        logging.info("Running check: %s", self.instruction)
        api_url, api_args = self.get_api_url_from_instruction(self.instruction)

        response = self.run_check(api_url, api_args)
        stdout, returncode = self.handle_agent_response(response)

        if stdout is None or returncode is None:
            raise ValueError("Stdout or returncode was None, cannot return "
                             "meaningfully.")

        # Get some info about the check
        current_time = time.time()
        accessor = api_url.replace('/api/', '').rstrip('/')

        # Save returned check results to the DB if we don't error out
        if listener.server.__INTERNAL__:
            db = listener.database.DB()
            db.add_check(accessor, current_time, current_time, int(returncode),
                         stdout, 'Internal', 'Passive')

        return stdout, returncode

    def run_check(self, api_url, api_args):
        """
        Access the local agent using api_url

        :param api_args: The dictionary containing the query string for the URL
        :type api_args: dict
        :param api_url: API URL that will be asked for the NCPA check
        :type api_url: unicode
        :return: A dict containing the standard out and return code of the
                 check
        :rtype: str
        """
        query = urllib.urlencode(api_args)
        complete_api_url = "{}?{}".format(api_url, query)

        logging.debug("Access the API with %s", complete_api_url)

        listener.server.__INTERNAL__ = True
        listener.server.listener.config['iconfig'] = self.config
        api_server = listener.server.listener.test_client()

        try:
            response = api_server.get(complete_api_url)
            response_json = response.data
        except AttributeError:
            response_json = '{}'

        return response_json

    def needs_to_run(self):
        """
        Check if we need to run the check again, or if it was ran within it's duration
        """
        key = hashlib.sha256(self.hostname + self.servicename).hexdigest()
        nrun = NEXT_RUN[key]

        logging.debug('Next run set to be at %s', nrun)
        if nrun <= time.time():
            return True
        return False

    def set_next_run(self, run_time):
        """
        Set next run time to the duration given or the default duration set in ncpa.cfg
        """
        key = hashlib.sha256(self.hostname + self.servicename).hexdigest()

        NEXT_RUN[key] = run_time + self.duration
        logging.debug('Next run is %s', NEXT_RUN[key])
        return

    @staticmethod
    def handle_agent_response(response):
        """
        Convert the response JSON into a Nagios check result.

        :return: A tuple containing the stdout and returncode, in that order.
        :rtype: tuple
        :param response: The JSON response from the local agent.
        :type response: unicode
        """
        logging.debug("Handling JSON response: %s", response)
        stdout, returncode = None, None

        try:
            response_dict = json.loads(response)
            stdout = response_dict['stdout']
            returncode = unicode(response_dict['returncode'])
        except ValueError as exc:
            logging.error("Error with JSON: %s. JSON was: %s", str(exc), response)
        except TypeError as exc:
            logging.error("Error response was not a string: %s", str(exc))

        logging.debug("JSON response handled found stdout='%s', returncode=%s",
                      stdout, returncode)

        return stdout, returncode

    @staticmethod
    def parse_cmdline_style_instruction(instruction):
        """
        Parse the commandline to support calls such as:

        /cpu/percent --warning 10 --critical 20 --delta 1

        As opposed to the URL encoded version

        :param instruction: The config entry that needs to parsed as a command
                            instruction
        :type instruction: unicode
        :return: tuple containing the API URL and a dictionary containing the
                 arguments
        :rtype: tuple
        """
        logging.debug("Parsing command line style instruction: %s",
                      instruction)
        stripped_instruction = instruction.strip().split(' ')

        api_url = stripped_instruction[0]
        api_args = {}

        arguments = stripped_instruction[1:]

        # Parse each individual variable, this will go through each command
        # line argument and get the argument names and their individual
        # variables.
        while arguments:

            argument = arguments.pop(0)
            if '=' in argument:
                arg_name, arg_value = argument.split('=', 1)
            else:
                try:
                    arg_name = argument
                    arg_value = arguments.pop(0)
                except IndexError:
                    logging.warning("Unable to parse all arguments from "
                                    "instruction. Mis-paired option: %s",
                                    argument)
                    break

            # We need to strip off the leading '--' or '-' if they exist as we
            # are using these flags as the literal variables we want to know
            # about.
            if arg_name.startswith('--'):
                arg_name = arg_name[2:]
            elif arg_name.startswith('-'):
                arg_name = arg_name[1:]

            api_args[arg_name] = arg_value

        return api_url, api_args

    @staticmethod
    def normalize_api_url(api_url):
        """
        Due to legacy concerns, we must support both /api/cpu/percent and
        cpu/percent. Notice the api_url passed to the actual listener must
        start with /api.

        :param api_url: The un-normalized api URL.
        :type api_url: unicode
        :rtype: unicode
        """
        if api_url.startswith('/api'):
            normalized = api_url
        elif api_url.startswith('api'):
            normalized = "/{}".format(api_url)
        elif api_url.startswith('/'):
            normalized = "/api{}".format(api_url)
        else:
            normalized = "/api/{}".format(api_url)

        if not normalized.endswith('/'):
            normalized += '/'

        return normalized

    @staticmethod
    def parse_api_url_style_instruction(instruction):
        parse = urlparse.urlparse(instruction)

        api_url = parse.path
        api_args = []

        # Parse arguments for URL
        args = urlparse.parse_qs(parse.query).items()
        for x, v in args:
            if len(v) == 1:
                api_args.append((x, v[0]))
            else:
                for val in v:
                    api_args.append((x, val))

        return api_url, api_args
