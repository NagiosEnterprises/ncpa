import checks
import json
import logging
import SocketServer

logger = logging.getLogger()

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(4096).strip()
        logging.debug('Received incoming connection. Info is: %s', self.data)
        jsondata = json.loads(self.data)
        logging.debug('JSON loaded from input.')
        try:
            returnstr = check_metric(jsondata)
        except Exception, e:
            logger.error('Exception was caught. %s' % str(e))
        self.request.sendall(returnstr)

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
    
    parser = optparse.OptionParser()
    
    parser.add_option('-w', '--warning')
    parser.add_option('-c', '--critical')
    
    options, args = parser.parse_args(shlex.split(arguments))
    
    warning = options.warning or ''
    critical = options.critical or ''
    
    return warning, critical

def check_metric(submitted_dict):
    '''
    Dispatch function that runs the proper metric, this function is
    what all queries get handed to.
    '''
    metric = submitted_dict.get('metric', '')
    warning = submitted_dict.get('warning', '')
    critical = submitted_dict.get('critical', '')
    arguments = submitted_dict.get('arguments', '')
    
    #~ if not warning and not critical and arguments:
        #~ try:
            #~ warning, critical = get_warn_crit_from_arguments(arguments)
        #~ except Exception, e:
            #~ logger.error('Exception raised. %s' % str(e))
        #~ logger.info('Warning: %s, Critical: %s' %(str(warning), str(critical)))
    
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
        item = checks.check_custom(item, metric, arguments)
        custom_plugin = True
    
    return item.to_json(custom_plugin)
