import environment
import subprocess
import tempfile
import os

def get_services():
    
    processes = {}
    
    if environment.SERVICE_TYPE == 'Windows':
        status = tempfile.TemporaryFile()
        processes = subprocess.Popen(['sc', 'query'], stdout=status)
        processes.wait()
        status.seek(0)
        
        service_name = None
        status = None
        
        for line in status.readlines():
            l = line.strip()
            if l.startswith('SERVICE_NAME'):
                service_name = l.split(maxpslit=1)[0]
            if l.startswith('STATE'):
                if 'RUNNING' in l:
                    status = 'running'
                else:
                    status = 'stopped'
                processes[service_name] = status
    
    if environment.SERVICE_TYPE = 'Linux':
        INIT_DIR = '/etc/init.d/'
        init_files = os.listdir(INIT_DIR)
        devnull = open(os.devnull, 'w')
        
        for f in init_files:
            if f != 'functions':
                script = os.path.join(INIT_DIR, f)
                service = subproces.Popen([script, 'status'], stdout=devnull, stderr=devnull)
                status = service.wait()
                if status == 0:
                    status = 'running'
                else:
                    status = 'stopped'
                processes[f] = status
    
    return services
