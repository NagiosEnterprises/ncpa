import checks
import json

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
        if self.unit in ['s','%','c','B','KB','GB']:
            unit = self.unit
        else:
            unit = ''
        perflist = ["%s=%s%s" % (self.nice, x, unit) for x in self.values]
        return ' '.join(perflist)
    
    def to_json(self):
        this_dict = {   "returncode" : self.get_return_code(),
                        "stdout" : self.get_stdout() }
        return json.dumps(this_dict)
    
    def get_return_code(self):
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
        import re
        #~ If its blank, return False so that it will always be OK
        if not trange:
            False
        #~ If its only a number
        is_match = re.match(r'^(\d+)$', trange)
        if is_match:
            tvalue = float(is_match.group(1))
            return value > tvalue
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
            preliminary = value > bottom and value < top
            if at:
                return not preliminary
            else:
                return preliminary

def check_metric(submitted_dict):
    
    metric = submitted_dict['metric']
    warning = submitted_dict.get('warning','')
    critical = submitted_dict.get('critical','')
    item = ReturnObject(warning=warning, critical=critical)
    
    if metric == 'check_cpu':
        item = checks.check_cpu(item)
    if metric == 'check_swap':
        item = checks.check_swap(item)
    if metric == 'check_memory':
        item = checks.check_memory(item)
    else:
        pass
    
    return item.to_json()
