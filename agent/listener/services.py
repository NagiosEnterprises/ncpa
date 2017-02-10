# -*- coding: utf-8 -*-

import nodes
import platform
import re
import subprocess
import tempfile
import os
import psutil
import server
import database
import time
from stat import ST_MODE,S_IXUSR,S_IXGRP,S_IXOTH

def filter_services(m):
    def wrapper(*args, **kwargs):
        services = m(*args, **kwargs)

        # Match type for services
        match = kwargs.get('match', None)
        if isinstance(match, list):
            match = match[0]

        # Service names (or partials to match)
        filtered_services = kwargs.get('service', [])
        if not isinstance(filtered_services, list):
            filtered_services = [filtered_services]

        # Filter by status (only really used for checks...)
        filter_statuses = kwargs.get('status', [])
        if not isinstance(filter_statuses, list):
            filter_statuses = [filter_statuses]

        if filtered_services or filter_statuses:
            accepted = {}

            # Match filters, do like, or regex
            if filtered_services:
                for service in filtered_services:
                    if match == 'search':
                        for s in services:
                            if service.lower() in s.lower():
                                accepted[s] = services[s]
                    elif match == 'regex':
                        for s in services:
                            if re.search(service, s):
                                accepted[s] = services[s]
                    else:
                        if service in services:
                            accepted[service] = services[service]
            
            # Match statuses
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

        if uname == 'Windows':
            return self.get_services_via_psutil
        elif uname == 'Darwin':
            return self.get_services_via_launchctl
        else:

            # look for systemd
            is_systemctl = False
            try:
                process = subprocess.Popen(['which', 'systemctl'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.wait()
                if process.returncode == 0:
                    is_systemctl = True
            except:
                pass

            # look for upstart
            is_upstart = False
            try:
                process = subprocess.Popen(['which', 'initctl'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process.wait()
                if process.returncode == 0:
                    is_upstart = True
            except:
                pass
        
            if is_systemctl:
                return self.get_services_via_systemctl
            elif is_upstart:
                return self.get_services_via_initctl
            else:
                # fall back on sysv init
                return self.get_services_via_initd

    @filter_services
    def get_services_via_psutil(self, *args, **kwargs):
        services = {}
        for service in psutil.win_service_iter():
            name = service.name()
            if service.status() == 'running':
                services[name] = 'running'
            else:
                services[name] = 'stopped'
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
        services = {}
        status = tempfile.TemporaryFile()
        service = subprocess.Popen(['systemctl', '--no-pager', '--no-legend', '--all', '--type=service', 'list-units'], stdout=status)
        service.wait()
        status.seek(0)

        for line in status.readlines():
            line.rstrip()
            unit, load, active, sub, description = re.split('\s+', line, 4)
            if unit.endswith('.service'):
                unit = unit[:-8]
            if 'not-found' not in load:
                if active.lower() == 'active' and sub.lower() != 'dead':
                    services[unit] = 'running'
                else:
                    services[unit] = 'stopped'
        return services

    @filter_services
    def get_services_via_initctl(self, *args, **kwargs):
        services = {}
        
        # Ubuntu & CentOS/RHEL 6 supports both sysv init and upstart
        services = self.get_services_via_initd(args, kwargs)

        # Now go ask initctl
        status = tempfile.TemporaryFile()
        service = subprocess.Popen(['initctl', 'list'], stdout=status)
        service.wait()
        status.seek(0)

        for line in status.readlines():
            m = re.match("(.*) (?:\w*)/(\w*)(?:, .*)?", line)
            try:
                if m.group(2) == 'running':
                    services[m.group(1)] = 'running'
                else:
                    services[m.group(1)] = 'stopped'
            except:
                pass
        return services

    # ---------------------------------
    # Special functions to test if a service is running or not
    # ---------------------------------

    def get_initd_service_status(self, service):
        p = subprocess.Popen(['service', service, 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode == 1:
            return 'stopped' # Service not found
        elif p.returncode == 0:
            out = out.lower()
            if not out:
                return 'running' # Service is likely running (no output but return 0)
            elif out in 'not running' or out in 'stopped': # Service returned 0 but had 'stopped' or 'not running' message
                return 'stopped'
            else:
                return 'running' # Service is assumed running due to (return 0)
        return 'stopped' # Service is likely not running (return > 0)

    @filter_services
    def get_services_via_initd(self, *args, **kwargs):
        # Only look at executable files in init.d (there is no README service)
        try:
            possible_services = filter(lambda x: os.stat('/etc/init.d/'+x)[ST_MODE] & (S_IXUSR|S_IXGRP|S_IXOTH), os.listdir('/etc/init.d'))
        except OSError as ex:
            pass

        services = {}
        devnull = open(os.devnull, 'w')

        for service in possible_services:
            status = 'stopped'

            # Skip broken 'services' that actually run when called with 'status'
            if 'rcS' in service:
                continue

            # Check if service is running via 'ps' since its faster that calling 'service'
            grep_search = '[%s]%s' % (service[0], service[1:])
            ps_call = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
            grep_call = subprocess.Popen(['grep', grep_search], stdout=devnull, stdin=ps_call.stdout)
            ps_call.wait()
            ps_call.stdout.close()
            grep_call.wait()

            if grep_call.returncode == 0:
                status = 'running'

            # Verify with 'service' if status is still stopped
            if status == 'stopped': 
                status = self.get_initd_service_status(service)

            services[service] = status

        devnull.close()
        return services

    def walk(self, *args, **kwargs):
        if kwargs.get('first', True):
            self.method = self.get_service_method(*args, **kwargs)
            return {self.name: self.method(*args, **kwargs)}
        else:
            return {self.name: []}

    @staticmethod
    def get_target_status(request_args):
        target_status = request_args.get('status', [])
        if not isinstance(target_status, list):
            target_status = [target_status]
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
        target_status = self.get_target_status(kwargs)
        method = self.get_service_method(*args, **kwargs)

        # Default to running status, so it will alert on not running
        if not target_status:
            target_status = 'running'

        # Remove status from kwargs since we use it for checking service status
        kwargs['status'] = ''

        services = method(*args, **kwargs)
        returncode = 0
        status = 'not a problem'
        stdout_builder = []

        if services:
            for service in services:
                priority = 0
                status = services[service]
                builder = '%s is %s' % (service, status)
                if not status in target_status:
                    priority = 1
                    builder = '%s (should be %s)' % (builder, ''.join(target_status))

                if priority > returncode:
                    returncode = priority

                stdout_builder.append({ 'info': builder, 'priority': priority })

            if returncode > 0:
                returncode = 2

            stdout = self.make_stdout(returncode, stdout_builder)
        else:
            returncode = 3
            stdout = "UNKNOWN: No services selected with 'service' value given"

        # Get the check logging value
        try:
            check_logging = int(kwargs['config'].get('general', 'check_logging'))
        except Exception as e:
            check_logging = 1

        # Put check results in the check database
        if not server.__INTERNAL__ and check_logging == 1:
            db = database.DB()
            dbc = db.get_cursor()
            current_time = time.time()
            data = (kwargs['accessor'].rstrip('/'), current_time, current_time, returncode,
                    stdout, kwargs['remote_addr'], 'Active')
            dbc.execute('INSERT INTO checks VALUES (?, ?, ?, ?, ?, ?, ?)', data)
            db.commit()

        return { 'stdout': stdout, 'returncode': returncode }

def get_node():
    return ServiceNode('services', None)
