import logging
import json
import urllib
import urlparse
import listener.server


class NCPACheck(object):
    """
    This class is meant to simplify the creation of other classes that simply run a
    command and return it to Nagios is some format. The immediate motivation for this
    is the difference between NSCA and NRDP. They share a lot of functionality that would
    be otherwise duplicated and should not be in the abstract class.

    Convenience class for wrapping up the commands defined in the config and setting their host/service to be accessed
    by their child classes and running the results.
    """

    def __init__(self, instruction, hostname, servicename):
        logging.debug('Initializing NCPA check with %s', instruction)
        self.hostname = hostname
        self.servicename = servicename
        self.instruction = instruction

    @staticmethod
    def get_api_url_from_instruction(instruction):
        """
        Method to parse the instruction in the config for running an NCPA check

        :param instruction: The instruction to be parsed
        :type instruction: unicode
        :return: Tuple containing the API URL that will be accessed to retrieve information from the local agent and its args
        :rtype:  tuple
        """
        logging.debug('Getting API url for instruction %s', instruction)

        if ' ' in instruction:
            api_url, api_args = NCPACheck.parse_cmdline_style_instruction(instruction)
        else:
            api_url, api_args = NCPACheck.parse_api_url_style_instruction(instruction)

        # Ensure we are running a check
        api_args['check'] = '1'
        api_url = NCPACheck.normalize_api_url(api_url)

        logging.debug('Determined instruction to be: %s', instruction)
        return api_url, api_args

    def run(self):
        """
        The primary method for running an NCPA check. Once the method has been instantiated
        this is the only function you should run.

        :return: A tuple containing the stdout and returncode of the NCPA check
        :rtype: tuple
        :raise: Will raise ValueError when either the stdout or returncode are not a string
        :raises: ValueError
        """
        logging.info("Running check: %s", self.instruction)
        api_url, api_args = self.get_api_url_from_instruction(self.instruction)
        response = self.run_check(api_url, api_args)
        stdout, returncode = self.handle_agent_response(response)

        if stdout is None or returncode is None:
            raise ValueError("Stdout or returncode was None, cannot return meaningfully.")

        return stdout, returncode

    @staticmethod
    def run_check(api_url, api_args):
        """
        Access the local agent using api_url

        :param api_args: The dictionary containing the query string for the URL
        :type api_args: dict
        :param api_url: API URL that will be asked for the NCPA check
        :type api_url: unicode
        :return: A dict containing the standard out and return code of the check
        :rtype: dict
        """
        query = urllib.urlencode(api_args)
        complete_api_url = "{}?{}".format(api_url, query)

        logging.debug("Access the API with %s", complete_api_url)

        api_server = listener.server.listener.test_client()

        try:
            response = api_server.get(complete_api_url)
            response_json = response.data
        except AttributeError:
            response_json = '{}'

        return response_json

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
            response_dict = json.loads(response)['value']
            stdout = response_dict['stdout']
            returncode = unicode(response_dict['returncode'])
        except ValueError as exc:
            logging.error("Error with JSON: %s. JSON was: %s", str(exc), response)
        except TypeError as exc:
            logging.error("Error response was not a string: %s", str(exc))
        except KeyError as exc:
            logging.error("JSON was missing keyword: %s. JSON given: %s", str(exc), response)

        logging.debug("JSON response handled found stdout='%s', returncode=%s", stdout, returncode)
        return stdout, returncode

    @staticmethod
    def parse_cmdline_style_instruction(instruction):
        """
        Parse the commandline to support calls such as:

        /api/cpu/percent --warning 10 --critical 20 --delta 1

        As opposed to the URL encoded version

        :param instruction: The config entry that needs to parsed as a command instruction
        :type instruction: unicode
        :return: tuple containing the API URL and a dictionary containing the arguments
        :rtype: tuple
        """
        logging.debug("Parsing command line style instruction: %s", instruction)
        stripped_instruction = instruction.strip().split(' ')

        api_url = stripped_instruction[0]
        api_args = {}

        arguments = stripped_instruction[1:]

        # Parse each individual variable, this will go through each command line argument and get the argument names
        # and their individual variables.
        while arguments:

            argument = arguments.pop(0)
            if '=' in argument:
                arg_name, arg_value = argument.split('=', 1)
            else:
                try:
                    arg_name = argument
                    arg_value = arguments.pop(0)
                except IndexError:
                    logging.warning("Unable to parse all arguments from instruction. Mis-paired option: %s", argument)
                    break

            # We need to strip off the leading '--' or '-' if they exist
            # as we are using these flags as the literal variables we want to know about.
            if arg_name.startswith('--'):
                arg_name = arg_name[2:]
            elif arg_name.startswith('-'):
                arg_name = arg_name[1:]

            api_args[arg_name] = arg_value

        return api_url, api_args

    @staticmethod
    def normalize_api_url(api_url):
        """
        Due to legacy concerns, we must support both /api/cpu/percent and cpu/percent. Notice the api_url passed to
        the actual listener must start with /api.

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
        parsed = urlparse.urlparse(instruction)

        api_url = parsed.path
        api_args = {x: v[0] for x, v in urlparse.parse_qs(parsed.query).items()}

        return api_url, api_args