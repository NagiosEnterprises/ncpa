import nodes
import platform
import subprocess
import tempfile
import os


def filter_services(m):
    def wrapper(*args, **kwargs):
        services = m(*args, **kwargs)
        filtered_services = kwargs.get('service', [])
        filter_statuses = kwargs.get('status', [])
        if filtered_services or filter_statuses:
            accepted = {}
            if filtered_services:
                for service in filtered_services:
                    if service in services:
                        accepted[service] = services[service]
            if filter_statuses:
                for service in services:
                    if services[service] in filter_statuses:
                        accepted[service] = services[service]
            return accepted
        return services
    return wrapper


class ServiceNode(nodes.LazyNode):

    def get_service_method(self, *args, **kwargs):
        uname = platform.uname()[0]
        try:
            process = subprocess.Popen(['which', 'systemctl'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.wait()
            if process.returncode == 0:
                is_systemctl = True
            else:
                is_systemctl = False
        except:
            is_systemctl = False

        if uname == 'Windows':
            return self.get_services_via_sc
        elif uname == 'Darwin':
            return self.get_services_via_launchctl
        else:
            if is_systemctl:
                return self.get_services_via_systemctl
            else:
                return self.get_services_via_initd

    @filter_services
    def get_services_via_sc(self, *args, **kwargs):
        services = {}
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
        return services

    @filter_services
    def get_services_via_launchctl(self, *args, **kwargs):
        services = {}
        status = tempfile.TemporaryFile()
        service = subprocess.Popen(['launchctl', 'list'], stdout=status)
        service.wait()
        status.seek(0)
        # The first line is the header
        status.readline()

        for line in status.readlines():
            pid, status, label = line.split()
            if pid == '-':
                services[label] = 'stopped'
            elif status == '-':
                services[label] = 'running'
        return services

    @filter_services
    def get_services_via_systemctl(self, *args, **kwargs):
        return {}

    @filter_services
    def get_services_via_initd(self, *args, **kwargs):
        possible_services = os.listdir('/etc/init.d')
        services = {x: 'stopped' for x in possible_services}
        devnull = open(os.devnull, 'w')

        for service in possible_services:
            grep_search = '[%s]%s' % (service[0], service[1:])
            ps_call = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
            grep_call = subprocess.Popen(['grep', grep_search], stdout=devnull, stdin=ps_call.stdout)
            ps_call.wait()
            ps_call.stdout.close()
            grep_call.wait()

            if grep_call.returncode == 0:
                services[service] = 'running'

        devnull.close()
        return services

    def walk(self, *args, **kwargs):
        if kwargs.get('first', True):
            self.method = self.get_service_method(*args, **kwargs)
            return {self.name: self.method(*args, **kwargs)}
        else:
            return {self.name: []}

    @staticmethod
    def get_service_name(request_args):
        service_name = request_args.get('service', [])
        return service_name

    @staticmethod
    def get_target_status(request_args):
        target_status = request_args.get('status', [])
        return target_status

    @staticmethod
    def make_stdout(returncode, stdout_builder):
        if returncode == 0:
            prefix = 'OK'
        else:
            prefix = 'CRITICAL'

        prioritized_stdout = sorted(stdout_builder, key=lambda x: x['priority'], reverse=True)
        info_line = ', '.join([x['info'] for x in prioritized_stdout])

        stdout = '%s: %s' % (prefix, info_line)
        return stdout

    def run_check(self, *args, **kwargs):
        service_names = self.get_service_name(kwargs)
        target_statuses = self.get_target_status(kwargs)
        method = self.get_service_method(*args, **kwargs)

        if not service_names:
            return {'stdout': 'OK: No services requested. That was too easy, give me something to do.', 'returncode': 0}

        services = method(*args, **kwargs)
        returncode = 0
        status = 'not a problem'
        stdout_builder = []
        for service in service_names:
            priority = 0
            if service in services:
                status = services[service]
                builder = 'Service %s is %s' % (service, status)
                if not status in target_statuses:
                    priority = 1
            else:
                priority = 2
                builder = 'Service %s was not found' % service

            if priority > returncode:
                returncode = priority

            stdout_builder.append({'info': builder, 'priority': priority})

        if returncode > 0:
            returncode = 2
        stdout = self.make_stdout(returncode, stdout_builder)
        return {'stdout': stdout, 'returncode': returncode}


def get_node():
    return ServiceNode('services', None)
