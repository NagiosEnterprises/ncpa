#!/usr/bin/env python3


import fnmatch
import json
import jsonschema
import logging
import os
import requests
import time


TEST_TARGET = os.environ['NCPA_TEST_TARGET']


class APITest(object):
    API_TEST_FILE_NAME = 'API_TEST'
    TEST_NAME_FILE = 'API_TEST'
    TEST_URL_FILE = 'url'
    TEST_SCHEMA_FILE = 'schema'
    TEST_RESPONSE_FILE = 'response'

    def __init__(self, directory):
        self.directory = directory

        self.test_name = None
        self.test_url = None
        self.test_schema = None

    @staticmethod
    def is_api_test(directory):
        return os.path.isfile(os.path.join(directory,
                                           APITest.API_TEST_FILE_NAME))

    def __enter__(self):
        logging.debug("Enter test %s", self.directory)

        s = os.path.join(self.directory, self.TEST_NAME_FILE)
        with open(s, 'r') as f:
            self.test_name = f.readline().strip()

        s = os.path.join(self.directory, self.TEST_URL_FILE)
        with open(s, 'r') as f:
            self.test_url = f.readline().strip()

        try:
            s = os.path.join(self.directory, self.TEST_SCHEMA_FILE)
            with open(s, 'r') as f:
                self.test_schema = json.load(f)
        except FileNotFoundError:
            self.test_schema = None

        try:
            s = os.path.join(self.directory, self.TEST_RESPONSE_FILE)
            with open(s, 'r') as f:
                self.test_response = f.readline().strip()
        except FileNotFoundError:
            self.test_response = None

        return self

    def __exit__(self, *args, **kwargs):
        logging.debug("Done running test %s", self.directory)


class APIContext(object):
    """Meant to just wrap whatever information we need to connect and get
    information, don't want to have to handle this in the APIRunner object.

    """

    @property
    def port(self):
        return os.environ.get(TEST_TARGET + '_PORT')

    @property
    def addr(self):
        return os.environ.get(TEST_TARGET + '_ADDR')

    @property
    def protocol(self):
        return 'https'

    @property
    def base_url(self):
        return '{protocol}://{addr}:{port}'.format(protocol=self.protocol,
                                                   addr=self.addr,
                                                   port=self.port)


class TestResult(object):

    def __init__(self, test_name):
        self.test_name = test_name

        self.success = None
        self.failure = None
        self.error = None

        self.message = None
        self.elapsed = 0

    def __repr__(self):
        printable = []
        if self.success:
            printable.append('SUCCESS')
        elif self.failure:
            printable.append('FAILURE')
        elif self.error:
            printable.append('ERROR')

        printable.append(self.test_name)
        printable.append(self.message)
        printable.append('Elapsed {0:.4}s'.format(self.elapsed))

        return ' -- '.join(printable)


class APIRunner(object):

    def __init__(self, api_test, context=None):
        self.api_test = api_test

        if context is None:
            context = APIContext()

        self.context = context
        self._response = None

        self.result = TestResult(api_test.test_name)

    @property
    def test_url(self):
        return '{base_url}/{api_target}'.format(base_url=self.context.base_url,
                                                api_target=self.api_test.test_url)

    @property
    def test_response(self):
        if self._response is None:
            self._response = requests.get(self.test_url,
                                          allow_redirects=True,
                                          verify=False)
        return self._response

    @property
    def test_response_text(self):
        return self.test_response.text

    @property
    def test_response_json(self):
        return json.loads(self.test_response.text)

    @property
    def test_response_is_well_formed(self):
        if self.api_test.test_schema:
            jsonschema.validate(self.test_response_json,
                                self.api_test.test_schema)
        return True

    def run(self):
        start = time.time()
        try:
            self.test_response_is_well_formed
            self.result.success = True
            self.result.message = 'Passed'
        except jsonschema.ValidationError as e:
            self.result.failure = True
            self.result.message = str(e)
        except Exception as e:
            self.result.error = True
            self.result.message = str(e)

        self.result.elapsed = time.time() - start


class TestFinder(object):

    def __init__(self, pattern='*', base_path='/tests'):
        self.pattern = pattern
        self.base_path = base_path

    @property
    def test_directories(self):
        for directory, _, _ in os.walk(self.base_path):
            if fnmatch.fnmatch(directory, self.pattern) and \
               APITest.is_api_test(directory):
                yield directory


def main():

    test_finder = TestFinder()
    api_context = APIContext()
    results = []

    for api_test_directory in test_finder.test_directories:
        with APITest(api_test_directory) as api_test:
            test_runner = APIRunner(api_test, api_context)
            test_runner.run()

            results.append(test_runner.result)
            print(test_runner.result)


if __name__ == "__main__":
    main()
