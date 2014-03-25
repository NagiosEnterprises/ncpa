from . import environment
import subprocess
import tempfile
import os
import platform

def get_services():
    
    services = {}
    
    if environment.SERVICE_TYPE == 'Windows':
        status = tempfile.TemporaryFile()
        service = subprocess.Popen(['sc', 'query', 'type=', 'service', 'state=', 'all'], stdout=status)
        service.wait()
        status.seek(0)
        
        for line in status.readlines():
            l = line.strip()
            if l.startswith('SERVICE_NAME'):
                service_name = l.split(' ', 1)[1]
            if l.startswith('STATE'):
                if 'RUNNING' in l:
                    status = 'running'
                else:
                    status = 'stopped'
                services[service_name] = status
    
    if environment.SERVICE_TYPE == 'Initd':
        INIT_DIR = '/etc/init.d/'
        init_files = os.listdir(INIT_DIR)
        devnull = open(os.devnull, 'w')
        
        for f in init_files:
            if f != 'functions':
                script = os.path.join(INIT_DIR, f)
                service = subprocess.Popen([script, 'status'], stdout=devnull, stderr=devnull)
                status = service.wait()
                if status == 0:
                    status = 'running'
                else:
                    status = 'stopped'
                services[f] = status

    if environment.SERVICE_TYPE == 'Darwin':
        cmd = 'launchctl'
        tmp = tempfile.TemporaryFile()

        service = subprocess.Popen([cmd, 'list'], stdout=tmp)
        service.wait()

        tmp.seek(0)
        # The first line is the header
        tmp.readline()

        for line in tmp.readlines():
            pid, status, label = line.split()
            if pid == '-':
                services[label] = 'stopped'
            elif status == '-':
                services[label] = 'running'

    return services
