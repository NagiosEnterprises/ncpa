from . import environment
import subprocess
import tempfile
import os
import platform
from io import open

def get_services():
    
    services = {}
    
    if environment.SERVICE_TYPE == u'Windows':
        status = tempfile.TemporaryFile()
        service = subprocess.Popen([u'sc', u'query', u'type=', u'service', u'state=', u'all'], stdout=status)
        service.wait()
        status.seek(0)
        
        for line in status.readlines():
            l = line.strip()
            if l.startswith(u'SERVICE_NAME'):
                service_name = l.split(u' ', 1)[1]
            if l.startswith(u'STATE'):
                if u'RUNNING' in l:
                    status = u'running'
                else:
                    status = u'stopped'
                services[service_name] = status
    
    if environment.SERVICE_TYPE == u'Initd':
        INIT_DIR = u'/etc/init.d/'
        init_files = os.listdir(INIT_DIR)
        devnull = open(os.devnull, u'w')
        
        for f in init_files:
            if f != u'functions':
                script = os.path.join(INIT_DIR, f)
                service = subprocess.Popen([script, u'status'], stdout=devnull, stderr=devnull)
                status = service.wait()
                if status == 0:
                    status = u'running'
                else:
                    status = u'stopped'
                services[f] = status

    if environment.SERVICE_TYPE == u'Darwin':
        cmd = u'launchctl'
        tmp = tempfile.TemporaryFile()

        service = subprocess.Popen([cmd, u'list'], stdout=tmp)
        service.wait()

        tmp.seek(0)
        # The first line is the header
        tmp.readline()

        for line in tmp.readlines():
            pid, status, label = line.split()
            if pid == u'-':
                services[label] = u'stopped'
            elif status == u'-':
                services[label] = u'running'

    return services
