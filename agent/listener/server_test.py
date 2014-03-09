import unittest
from . import server
import configparser
import json
import os
import urllib.request, urllib.parse, urllib.error
import pickle

curpath = os.getcwd()
runpath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def is_json(data):
    try:
        rv = json.loads(data)
    except ValueError:
        return False
    return True

def has_no_errors(data):
    rv = json.loads(data)
    if 'error' in rv:
        return False
    return True

def is_valid_result(data):
    rv = json.loads(data)
    va = rv.get('value', {})
    ret = va.get('returncode', None)
    std = va.get('stdout', None)
    return is_json(data) and has_no_errors(data) and ret != None and std != None

def stdout_contains(data, item):
    rv = json.loads(data)
    va = rv.get('value', {})
    ret = va.get('stdout', '')
    return item in ret

def returncode_is(data, item):
    rv = json.loads(data)
    va = rv.get('value', {})
    ret = va.get('returncode', '')
    return item == ret

class TestServerFunctions(unittest.TestCase):
    
    def setUp(self):
        self.config = configparser.ConfigParser()
        self.config.read('../agent/etc/ncpa.cfg')
        self.token = self.config.get('api', 'community_string')
        server.listener.config['TESTING'] = True
        server.listener.config['iconfig'] = self.config
        self.app = server.listener.test_client()
    
    def authorize_url(self, url, token=None, **kwargs):
        '''Helper function that will authorize a URL with the proper
        token.
        
        url - The URL you want to authorize
        token - The token to be used. If none is given, it will use the token
                specified in the config
        first_variable - Defaults to true. If false is given, it will assume
                         there exists other get params before and will use
                         an ampersand rather than a question for delimiting.
        '''
        if token == None:
            token = self.token
        kwargs['token'] = token
        get_parms = urllib.parse.urlencode(kwargs)
        return self.app.get('%s?%s' % (url, get_parms), follow_redirects=True).data

class TestLoginFunctions(TestServerFunctions):
    
    def test_authentication_correct(self):
        '''Check for proper authentication with good token.'''
        rv = self.authorize_url('/')
        assert 'Incorrect credentials' not in rv
    
    def test_authentication_fails(self):
        '''Check for failed authentication with bad token.'''
        rv = self.authorize_url('/', self.token + 's')
        assert is_json(rv) and not has_no_errors(rv)
    

class SaveConfig(unittest.TestCase):
    
    def setUp(self):
        f = open('/tmp/test.pkl')
        self.config = pickle.load(f)
        f.close()
    
    def tearDown(self):
        del self.config
    
    def test_vivicate_dict(self):
        test = {'a|b|c': [0]}
        expected = {'a': {'b|c': [0]}}
        result = server.vivicate_dict(test)
        assert result == expected
    
    def test_save_config_simple(self):
        conf = server.save_config(self.config, '/tmp/test.cfg')
        assert conf.has_section('listener')
        assert conf.has_section('passive')
        assert conf.has_section('nrdp')
        assert conf.has_section('api')
        assert conf.has_section('nrds')
        assert conf.has_section('passive checks')
        assert conf.has_section('plugin directives')

class APIFunctions(TestServerFunctions):
    
    def setUp(self):
        super(APIFunctions, self).setUp()
        self.apiurl = '/api'
    
    def authorize_url(self, url, **kwargs):
        url = self.apiurl + url
        return super(APIFunctions, self).authorize_url(url, **kwargs)
    
    def test_api_ok(self):
        '''Check for well formed JSON tree upon call to /api/'''
        rv = self.authorize_url(self.apiurl)
        assert is_json(rv) and has_no_errors(rv)
    
    def test_api_check_on_tree(self):
        '''Ensure calling check on a non-leaf node returns JSON'''
        rv = self.authorize_url('', check=True)
        assert is_json(rv) and has_no_errors(rv)
    
    def test_api_make_check(self):
        '''Test CPU values are valid'''
        rv = self.authorize_url('/cpu/count', check=True)
        assert is_json(rv) and has_no_errors(rv) and is_valid_result(rv)
    
    def test_api_make_check_with_unit(self):
        '''Checking ability to make a check from a tree value with a unit associated with it'''
        rv = self.authorize_url('/cpu/system', check=True)
        assert is_valid_result(rv)
    
    def test_api_make_check_warning(self):
        '''Checking ability to ensure checks allow warnings.'''
        rv = self.authorize_url('/cpu/count', check=True, warning=0)
        assert is_valid_result(rv) and stdout_contains(rv, 'WARNING') and returncode_is(rv, 1)
    
    def test_run_plugin(self):
        '''Checking ability to run plugins'''
        TEST_PLUGIN = runpath + '/plugins/test.sh'
        with open(TEST_PLUGIN, 'w') as plugin:
            plugin.write('#!/bin/sh\n')
            plugin.write('echo "$1"\n')
            plugin.write('exit 2\n')
        rv = self.authorize_url('/agent/plugin/test.sh/hello')
        os.remove(TEST_PLUGIN)
        assert is_valid_result(rv) and stdout_contains(rv, 'hello') and returncode_is(rv, 2)
    
    def test_run_plugin_with_rule(self):
        '''Checking the ability to run plugins with a given rule.'''
        TEST_PLUGIN = runpath + '/plugins/test.random'
        with open(TEST_PLUGIN, 'w') as plugin:
            plugin.write('#!/bin/sh\n')
            plugin.write('echo "$1"\n')
            plugin.write('exit 2\n')
        self.config.set('plugin directives', '.random', '/bin/echo "All is well"')
        server.listener.config['iconfig'] = self.config
        rv = self.authorize_url('/agent/plugin/test.random/hello')
        os.remove(TEST_PLUGIN)
        assert is_valid_result(rv) and stdout_contains(rv, 'All is well')
    

if __name__ == '__main__':
    os.chdir(runpath)
    unittest.main()
    os.chdir(curpath)
