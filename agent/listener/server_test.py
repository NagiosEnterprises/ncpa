from __future__ import with_statement
import unittest
from . import server
import ConfigParser
import json
import os
import urllib
import pickle
from io import open

curpath = os.getcwdu()
runpath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_json(data):
    try:
        json.loads(data)
    except ValueError:
        return False
    return True


def has_no_errors(data):
    rv = json.loads(data)
    if u'error' in rv:
        return False
    return True


def is_valid_result(data):
    rv = json.loads(data)
    va = rv.get(u'value', {})
    ret = va.get(u'returncode', None)
    std = va.get(u'stdout', None)
    return is_json(data) and has_no_errors(data) and ret is not None and std is not None


def stdout_contains(data, item):
    rv = json.loads(data)
    va = rv.get(u'value', {})
    ret = va.get(u'stdout', u'')
    return item in ret


def returncode_is(data, item):
    rv = json.loads(data)
    va = rv.get(u'value', {})
    ret = va.get(u'returncode', u'')
    return item == ret


class TestServerFunctions(unittest.TestCase):

    def setUp(self):
        self.config = ConfigParser.ConfigParser()
        self.config.read(u'../agent/etc/ncpa.cfg')
        self.token = self.config.get(u'api', u'community_string')
        server.listener.config[u'TESTING'] = True
        server.listener.config[u'iconfig'] = self.config
        self.app = server.listener.test_client()

    def authorize_url(self, url, token=None, **kwargs):
        u'''Helper function that will authorize a URL with the proper
        token.

        url - The URL you want to authorize
        token - The token to be used. If none is given, it will use the token
                specified in the config
        first_variable - Defaults to true. If false is given, it will assume
                         there exists other get params before and will use
                         an ampersand rather than a question for delimiting.
        '''
        if token is None:
            token = self.token
        kwargs[u'token'] = token
        get_parms = urllib.urlencode(kwargs)
        return self.app.get(u'%s?%s' % (url, get_parms), follow_redirects=True).data


class TestLoginFunctions(TestServerFunctions):

    def test_authentication_correct(self):
        u'''Check for proper authentication with good token.'''
        rv = self.authorize_url(u'/')
        assert u'Incorrect credentials' not in rv

    def test_authentication_fails(self):
        u'''Check for failed authentication with bad token.'''
        rv = self.authorize_url(u'/', self.token + u's')
        assert is_json(rv) and not has_no_errors(rv)


class SaveConfig(unittest.TestCase):

    def setUp(self):
        f = open(u'/tmp/test.pkl')
        self.config = pickle.load(f)
        f.close()

    def tearDown(self):
        del self.config

    def test_vivicate_dict(self):
        test = {u'a|b|c': [0]}
        expected = {u'a': {u'b|c': [0]}}
        result = server.vivicate_dict(test)
        assert result == expected

    def test_save_config_simple(self):
        conf = server.save_config(self.config, u'/tmp/test.cfg')
        assert conf.has_section(u'listener')
        assert conf.has_section(u'passive')
        assert conf.has_section(u'nrdp')
        assert conf.has_section(u'api')
        assert conf.has_section(u'nrds')
        assert conf.has_section(u'passive checks')
        assert conf.has_section(u'plugin directives')


class APIFunctions(TestServerFunctions):

    def setUp(self):
        super(APIFunctions, self).setUp()
        self.apiurl = u'/api'

    def authorize_url(self, url, **kwargs):
        url = self.apiurl + url
        return super(APIFunctions, self).authorize_url(url, **kwargs)

    def test_api_ok(self):
        u'''Check for well formed JSON tree upon call to /api/'''
        rv = self.authorize_url(self.apiurl)
        assert is_json(rv) and has_no_errors(rv)

    def test_api_check_on_tree(self):
        u'''Ensure calling check on a non-leaf node returns JSON'''
        rv = self.authorize_url(u'', check=True)
        assert is_json(rv) and has_no_errors(rv)

    def test_api_make_check(self):
        u'''Test CPU values are valid'''
        rv = self.authorize_url(u'/cpu/count', check=True)
        assert is_json(rv) and has_no_errors(rv) and is_valid_result(rv)

    def test_api_make_check_with_unit(self):
        u'''Checking ability to make a check from a tree value with a unit associated with it'''
        rv = self.authorize_url(u'/cpu/system', check=True)
        assert is_valid_result(rv)

    def test_api_make_check_warning(self):
        u'''Checking ability to ensure checks allow warnings.'''
        rv = self.authorize_url(u'/cpu/count', check=True, warning=0)
        assert is_valid_result(rv) and stdout_contains(rv, u'WARNING') and returncode_is(rv, 1)

    def test_run_plugin(self):
        u'''Checking ability to run plugins'''
        TEST_PLUGIN = runpath + u'/plugins/test.sh'
        with open(TEST_PLUGIN, u'w') as plugin:
            plugin.write(u'#!/bin/sh\n')
            plugin.write(u'echo "$1"\n')
            plugin.write(u'exit 2\n')
        rv = self.authorize_url(u'/agent/plugin/test.sh/hello')
        os.remove(TEST_PLUGIN)
        assert is_valid_result(rv) and stdout_contains(rv, u'hello') and returncode_is(rv, 2)

    def test_run_plugin_with_rule(self):
        u'''Checking the ability to run plugins with a given rule.'''
        TEST_PLUGIN = runpath + u'/plugins/test.random'
        with open(TEST_PLUGIN, u'w') as plugin:
            plugin.write(u'#!/bin/sh\n')
            plugin.write(u'echo "$1"\n')
            plugin.write(u'exit 2\n')
        self.config.set(u'plugin directives', u'.random', u'/bin/echo "All is well"')
        server.listener.config[u'iconfig'] = self.config
        rv = self.authorize_url(u'/agent/plugin/test.random/hello')
        os.remove(TEST_PLUGIN)
        assert is_valid_result(rv) and stdout_contains(rv, u'All is well')


if __name__ == u'__main__':
    os.chdir(runpath)
    unittest.main()
    os.chdir(curpath)
