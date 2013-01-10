import checks
import json
import logging
import SocketServer
import BaseHTTPServer
import cgi
import urlparse
import requests
import frontend
import re
import html
import commands

logger = logging.getLogger()

class GenHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    
    def setup_response(self):
        self.directive = self.path.split('?', 1)[0]
        try:
            type(self.GET)
        except AttributeError:
            self.GET = {}
        try:
            type(self.POST)
        except AttributeError:
            self.POST = {}
        self.REQUEST = dict(self.GET.items() + self.POST.items())
    
    def respond(self, response):
        '''Convenience method to simple send a well formed HTTP response
        back to the requester.
        '''
        self.send_response(response.code)
        self.send_header('Content-type', response.header)
        self.end_headers()
        self.wfile.write(response.message)
    
    def do_check(self):
        '''Runs the check on the local server. Calls response() with
        the result.
        '''
        hp = html.HttpResponse()
        hp.header = 'application/json'
        try:
            hp.message = check_metric(self.REQUEST, self.server.config)
            hp.code = 200
        except Exception, e:
            logger.exception(e)
            hp.message = json.dumps({ 'error' : str(e)})
            hp.code = 500
        return hp
    
    def forward_request(self):
        '''Forwards request to parent NRDX
        '''
        forward_to = self.server.config.get('nrdp', 'parent')
        hp = html.HttpResponse()
        try:
            if self.request_method == 'get':
                response = requests.get(forward_to, params=self.REQUEST)
            else:
                response = requests.post(forward_to, params=self.REQUEST)
            hp.message = response.text
            hp.code = response.status_code
            hp.headers = response.headers['content-type']
        except Exception, e:
            hp.message = str(e)
            hp.code = 404
        return hp
    
    def handle_incoming(self):
        '''Gateway function meant to tie POST and GET together. If
        'cmd' is present in the REQUEST variable, it will forward the
        request to its parent, otherwise it will run the check
        '''
        self.setup_response()
        if re.search('^/nrdp', self.directive):
            response = self.forward_request()
        elif re.search('^/frontend', self.directive):
            response = frontend.handle(self)
        elif re.search('^/static', self.directive):
            res = re.search(r'^/static/(.*)\.(css|js)$', self.directive)
            response = html.HttpResponse()
            if res:
                directory = __file__.rsplit('/', 1)[0]
                filename = directory + '/static/%s.%s' % (res.group(1), res.group(2))
                try:
                    f = open(filename, 'r')
                    response.message = ''.join(f.readlines())
                    f.close()
                    if res.group(1) == 'css':
                        response.header = 'text/css'
                    elif res.group(1) == 'js':
                        response.header = 'application/javascript'
                except IOError, e:
                    logger.exception(e)
                    response.message = '%s was not readable.' % filename
                    response.code = 404
            else:
                response.message = 'No such file.'
                response.code = 403
        elif re.search('^/command', self.directive):
            response = handle_command(self)
        else:
            response = self.do_check()
        self.respond(response)
    
    def do_POST(self):
        logger.info('Processing request...')
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
            postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            postvars = {}
        self.request_method = 'post'
        self.POST = postvars
        try:
            self.handle_incoming()
        except Exception, e:
            self.handle_server_exception(e)
    
    def do_GET(self):
        
        parsed_path = urlparse.urlparse(self.path)
        self.GET = dict(urlparse.parse_qsl(parsed_path.query))
        self.request_method = 'get'
        try:
            self.handle_incoming()
        except Exception, e:
            self.handle_server_exception(e)
    
    def handle_server_exception(self, e):
        logger.exception(e)
        hp = html.HttpResponse()
        hp.message = str(e)
        hp.code = 500

def handle_command(request):
    hp = html.HttpResponse()
    hp.header = 'application/json'
    if not request.REQUEST.get('command'):
        hp.message = json.dumps({'errors':'No command given.'})
        hp.code = 400
    elif request.REQUEST.get('command') == 'enumerate_plugins':
        plugins = commands.enumerate_plugins()
        count = len(plugins)
        hp.message = json.dumps({'plugins' : plugins, 'count' : count})
    return hp
    
        

class ReturnObject(object):
    
    def __init__(self, values='', unit='', warning='', critical='', nice=''):
        #~ Make sure values is a list
        try:
            [x for x in values]
        except:
            values = [values]
        self.values = values
        self.unit   = unit
        self.critical = critical
        self.warning = warning
        self.nice = nice
    
    def set_values(self, values):
        try:
            [x for x in values]
        except:
            values = [values]
        self.values = values
    
    def set_stdout(self, stdout):
        self.stdout = stdout
    
    def get_stdout(self):
        '''
        Wrapper script to be run after the check method is run, returns
        the string to be put to stdout
        '''
        retcode = self.get_return_code()
        if retcode == 0:
            prefix = 'OK'
        elif retcode == 1:
            prefix = 'WARNING'
        elif retcode == 2:
            prefix = 'CRITICAL'
        else:
            prefix = 'UNKNOWN'
        if self.values:
            perfdata = self.get_perfdata()
            stdout =  prefix + ':' + self.stdout + " : " + ','.join(["%s%s" % (str(x), self.unit) for x in self.values])
            stdout += '|' + perfdata
            return stdout
        else:
            return 'Error running plugin.'
    
    def get_perfdata(self):
        '''
        Returns string representing relevant perfdata, Takes no arguments,
        returns perfdata string
        '''
        if self.unit in ['s','%','c','B','KB','GB']:
            unit = self.unit
        else:
            unit = ''
        perflist = ["%s=%s%s" % (self.nice, x, unit) for x in self.values]
        return ' '.join(perflist)
    
    def to_json(self, custom=False):
        '''
        Wraps the nagios check result in a JSON for returning to
        the server
        '''
        if not custom:
            this_dict = {   "returncode" : self.get_return_code(),
                            "stdout" : self.get_stdout() }
        else:
            this_dict = {   "returncode" : self.returncode,
                            "stdout"     : self.stdout }
        return json.dumps(this_dict)
    
    def get_return_code(self):
        '''
        Looks at the internal variables self.warning and self.critical
        and returns the proper nagios return code
        '''
        returncode = 0
        if self.warning:
            for value in self.values:
                if self.is_within_range(self.warning, value):
                    returncode = 1
        if self.critical:
            for value in self.values:
                if self.is_within_range(self.critical, value):
                    returncode = 2
        return returncode
    
    def is_within_range(self, trange, value):
        '''
        Given a string Nagios range code, and a return value from
        a plugin, returns true if value is withing the range value
        '''
        import re
        #~ If its blank, return False so that it will never trigger an alert
        if not trange:
            return False
        #~ If its only a number
        is_match = re.match(r'^(\d+)$', trange)
        if is_match:
            tvalue = float(is_match.group(1))
            return 0 >= value or value >= tvalue
        #~ If it contains a colon
        is_match = re.match(r'^(@?)(\d+|~):(\d*)$', trange)
        if is_match:
            at = is_match.group(1)
            try:
                bottom = float(is_match.group(2))
            except:
                bottom = float('-Inf')
            try:
                top = float(is_match.group(3))
            except:
                top = float('Inf')
            preliminary = value < bottom or value > top
            if at:
                return not preliminary
            else:
                return preliminary

def get_warn_crit_from_arguments(arguments):
    import optparse
    import shlex
    
    logger.debug('Parsing arguments: %s' % arguments)
    #~ Must give the arguments a prog name in order for them to work with
    #~ optparse
    arguments = str('./xxx ' + arguments)
    parser = optparse.OptionParser()
    parser.add_option('-w', '--warning')
    parser.add_option('-c', '--critical')
    try:
        arg_lat = shlex.split(arguments)
        logger.info(str(arg_lat))
        options, args = parser.parse_args(arg_lat)
    except:
        import traceback
        f = open('var/exception.txt', 'a')
        traceback.print_exc(file=f)
    warning = options.warning or ''
    critical = options.critical or ''
    return warning, critical

def check_metric(submitted_dict, config):
    '''
    Dispatch function that runs the proper metric, this function is
    what all queries get handed to.
    '''
    metric = submitted_dict.get('metric', '')
    warning = submitted_dict.get('warning', '')
    critical = submitted_dict.get('critical', '')
    arguments = submitted_dict.get('arguments', '')
    
    if not warning and not critical and arguments:
        warning, critical = get_warn_crit_from_arguments(arguments)
        logger.info('Warning: %s, Critical: %s' %(str(warning), str(critical)))
    
    try:
        item = ReturnObject(warning=warning, critical=critical)
    except Exception, e:
        logger.exception(e)
    
    logger.debug('Beginning execution for %s', metric)
    
    custom_plugin = False
    if metric == 'check_cpu':
        item = checks.check_cpu(item)
    elif metric == 'check_swap':
        item = checks.check_swap(item)
    elif metric == 'check_memory':
        item = checks.check_memory(item)
    else:
        item = checks.check_custom(item, metric, arguments, config)
        custom_plugin = True
    
    return item.to_json(custom_plugin)
