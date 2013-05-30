import unittest
import server
import ConfigParser
import json
import os
import urllib

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
        self.config = ConfigParser.ConfigParser()
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
        get_parms = urllib.urlencode(kwargs)
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
    

if __name__ == '__main__':
    os.chdir(runpath)
    unittest.main()
    os.chdir(curpath)
