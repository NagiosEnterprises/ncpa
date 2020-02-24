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
import logging
import Queue
from stat import ST_MODE,S_IXUSR,S_IXGRP,S_IXOTH
from threading import Timer

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
        elif uname == 'AIX':
            return self.get_services_via_lssrc
        elif uname == 'SunOS':
            return self.get_services_via_svcs
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

        # Check to see if there are any services we need to add that
        # weren't already caught by the initd script check
        for line in status.readlines():
            m = re.match("(.*) (?:\w*)/(\w*)(?:, .*)?", line)
            try:
                if m.group(1) not in services:
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

    def kill_proc(self, p):
        p.kill()

    def get_initd_service_status(self, service):
        service_status = subprocess.Popen(['service', service, 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timer = Timer(2, self.kill_proc, [service_status])

        # Stop subprocess if it takes more then 2 seconds to get service status
        try:
            timer.start()
            stdout, stderr = service_status.communicate()
        finally:
            timer.cancel()

        out = stdout.lower()
        if 'not running' in out or 'stopped' in out:
            return 'stopped'

        # Return stopped if return code is 1-3
        if service_status.returncode in range(1, 3):
            return 'stopped'
        elif service_status.returncode == 0:
            return 'running'

        # Service is likely not running (return > 0)
        return 'unknown'

    @filter_services
    def get_services_via_initd(self, *args, **kwargs):
        # Only look at executable files in init.d (there is no README service)
        try:
            possible_services = filter(lambda x: os.stat('/etc/init.d/'+x)[ST_MODE] & (S_IXUSR|S_IXGRP|S_IXOTH), os.listdir('/etc/init.d'))
        except OSError as e:
            logging.exception(e);
            pass

        services = {}
        processes = []
        for p in psutil.process_iter(attrs=['name']):
            processes.append(p.info['name'])

        for service in possible_services:
            status = 'unknown'

            # Skip broken 'services' that actually run when called with 'status'
            if 'rcS' in service:
                continue

            # Do a quick check if there is a process for this service running
            for p in processes:
                if service == p:
                    status = 'running'

            # Verify with 'service' if status is still stopped
            if status == 'unknown': 
                status = self.get_initd_service_status(service)

            services[service] = status

        return services

    # AIX-specific list services section
    @filter_services
    def get_services_via_lssrc(self, *args, **kwargs):
        services = {}
        status = tempfile.TemporaryFile()
        service = subprocess.Popen(['lssrc', '-a'], stdout=status)
        service.wait()
        status.seek(0)

        # The first line is the header
        status.readline()

        for line in status.readlines():
            ls = line.split()
            sub = ls[0]
            status = ls[-1]
            if status == 'active':
                services[sub] = 'running'
            elif status == 'inoperative':
                services[sub] = 'stopped'
            else:
                services[sub] = 'unknown'

        return services

    # Solaris specific svcs command to get services
    @filter_services
    def get_services_via_svcs(self, *args, **kwargs):
        services = {}
        status = tempfile.TemporaryFile()
        service = subprocess.Popen(['svcs', '-a', '-o', 'STATE,FMRI'], stdout=status)
        service.wait()
        status.seek(0)

        # The first line is the header
        status.readline()

        for line in status.readlines():
            ls = line.split()

            # Skip lrc items
            if 'lrc:/' in ls[1]:
                continue 

            sub = ls[1].replace('svc:/', '').replace('/', '|')
            status = ls[0]
            if status == 'online':
                services[sub] = 'running'
            elif 'offline' in status or status == 'maintenance' or status == 'disabled':
                services[sub] = 'stopped'
            else:
                services[sub] = 'unknown'

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
        elif returncode == 2:
            prefix = 'CRITICAL';
        else:
            prefix = 'UNKNOWN'

        prioritized_stdout = sorted(stdout_builder, key=lambda x: x['priority'], reverse=True)
        info_line = ', '.join([x['info'] for x in prioritized_stdout])

        stdout = '%s: %s' % (prefix, info_line)
        return stdout

    def run_check(self, *args, **kwargs):
        target_status = self.get_target_status(kwargs)
        method = self.get_service_method(*args, **kwargs)

        # Get a list of all services to be looking for
        filtered_services = kwargs.get('service', [])
        if not isinstance(filtered_services, list):
            filtered_services = [filtered_services]

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

                # Remove each service with status from filtered_services to find out if we are missing some
                i = filtered_services.index(service)
                filtered_services.pop(i)

                if priority > returncode:
                    returncode = priority

                stdout_builder.append({ 'info': builder, 'priority': priority })

            if returncode > 0:
                returncode = 2

            if filtered_services:
                for service in filtered_services:
                    stdout_builder.append({ 'info': '%s could not be found' % service, 'priority': 0 })
                returncode = 3

            stdout = self.make_stdout(returncode, stdout_builder)
        else:
            returncode = 3   
            stdout = "UNKNOWN: No services found for service names: %s" % ', '.join(filtered_services)

        # Get the check logging value
        try:
            check_logging = int(kwargs['config'].get('general', 'check_logging'))
        except Exception as e:
            check_logging = 1

        # Put check results in the check database
        if not server.__INTERNAL__ and check_logging == 1:
            db = database.DB()
            current_time = time.time()
            db.add_check(kwargs['accessor'].rstrip('/'), current_time, current_time, returncode,
                         stdout, kwargs['remote_addr'], 'Active')

        return { 'stdout': stdout, 'returncode': returncode }

def get_node():
    return ServiceNode('services', None)
