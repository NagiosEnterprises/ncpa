import psutil
import nodes
import logging
import re
import platform
import tempfile
import subprocess


class ProcessNode(nodes.LazyNode):

    @staticmethod
    def get_exe(request_args):
        exe = request_args.get('exe', [])
        if not isinstance(exe, list):
            exe = [exe]
        return exe

    @staticmethod
    def get_username(request_args):
        username = request_args.get('username', [])
        if not isinstance(username, list):
            username = [username]
        return username

    @staticmethod
    def get_name(request_args):
        name = request_args.get('name', [])
        if not isinstance(name, list):
            name = [name]
        return name

    @staticmethod
    def get_cmd(request_args):
        cmd = request_args.get('cmd', [])
        if not isinstance(cmd, list):
            cmd = [cmd]
        return cmd

    @staticmethod
    def get_count(request_args):
        count = request_args.get('count', 0)
        if isinstance(count, list):
            count = count[0]
        return int(count)

    @staticmethod
    def get_sleep(request_args):
        sleep = request_args.get('sleep', None)
        if sleep:
            if isinstance(sleep, list):
                sleep = float(sleep[0])
        return sleep

    @staticmethod
    def get_cpu_percent(request_args):
        cpu_percent = request_args.get('cpu_percent', None)
        if cpu_percent:
            if isinstance(cpu_percent, list):
                cpu_percent = float(cpu_percent[0])
        return cpu_percent

    @staticmethod
    def get_mem_percent(request_args):
        mem_percent = request_args.get('mem_percent', None)
        if mem_percent:
            if isinstance(mem_percent, list):
                mem_percent = float(mem_percent[0])
        return mem_percent

    @staticmethod
    def get_mem_rss(request_args):
        mem_rss = request_args.get('mem_rss', None)
        if mem_rss:
            if isinstance(mem_rss, list):
                mem_rss = float(mem_rss[0])
        return mem_rss

    @staticmethod
    def get_mem_vms(request_args):
        mem_vms = request_args.get('mem_vms', None)
        if mem_vms:
            if isinstance(mem_vms, list):
                mem_vms = float(mem_vms[0])
        return mem_vms

    @staticmethod
    def get_combiner(request_args):
        combiner = request_args.get('combiner', 'and')
        if isinstance(combiner, list):
            combiner = combiner[0]
        if combiner == 'or':
            return any
        else:
            return all

    @staticmethod
    def get_match(request_args):
        match = request_args.get('match', None)
        if match:
            if isinstance(match, list):
                match = match[0]
        return match

    def make_filter(self, *args, **kwargs):
        exes = self.get_exe(kwargs)
        usernames = self.get_username(kwargs)
        names = self.get_name(kwargs)
        cmds = self.get_cmd(kwargs)
        cpu_percent = self.get_cpu_percent(kwargs)
        mem_percent = self.get_mem_percent(kwargs)
        comparison = self.get_combiner(kwargs)
        mem_rss = self.get_mem_rss(kwargs)
        mem_vms = self.get_mem_vms(kwargs)
        match = self.get_match(kwargs)

        def proc_filter(process):
            comp = []

            for exe in exes:
                if match == 'search':
                    if exe.lower() in process['exe'].lower():
                        comp.append(True)
                    else:
                        comp.append(False)
                elif match == 'regex':
                    if re.search(exe, process['exe']):
                        comp.append(True)
                    else:
                        comp.append(False)
                else:
                    if process['exe'].lower() == exe.lower():
                        comp.append(True)
                    else:
                        comp.append(False)

            for username in usernames:
                if match == 'search':
                    if username.lower() in process['username'].lower():
                        comp.append(True)
                    else:
                        comp.append(False)
                elif match == 'regex':
                    if re.search(username, process['username']):
                        comp.append(True)
                    else:
                        comp.append(False)
                else:
                    if process['username'].lower() == username.lower():
                        comp.append(True)
                    else:
                        comp.append(False)

            for name in names:
                if match == 'search':
                    if name.lower() in process['name'].lower():
                        comp.append(True)
                    else:
                        comp.append(False)
                elif match == 'regex':
                    if re.search(name, process['name']):
                        comp.append(True)
                    else:
                        comp.append(False)
                else:
                    if process['name'].lower() == name.lower():
                        comp.append(True)
                    else:
                        comp.append(False)

            for cmd in cmds:
                process_cmd = process['cmd'].lower()
                if not process_cmd:
                    comp.append(False)
                else:
                    if match == 'search':
                        if cmd.lower() in process['cmd'].lower():
                            comp.append(True)
                        else:
                            comp.append(False)
                    elif match == 'regex':
                        if re.search(cmd, process['cmd']):
                            comp.append(True)
                        else:
                            comp.append(False)
                    else:
                        if process['cmd'].lower() == cmd.lower():
                            comp.append(True)
                        else:
                            comp.append(False)

            if not cpu_percent is None:
                comp.append(cpu_percent <= process['cpu_percent'][0])

            if not mem_percent is None:
                comp.append(mem_percent <= process['mem_percent'][0])

            if not mem_rss is None:
                comp.append(mem_rss <= process['mem_rss'][0])

            if not mem_vms is None:
                comp.append(mem_vms <= process['mem_vms'][0])

            return comparison(comp)

        return proc_filter

    @staticmethod
    def standard_form(self, process, ps_procs, units='', sleep=None):
        pid = str(process.pid)

        try:
            if pid in ps_procs:
                proc = ps_procs.get(pid)
                cmd = proc[2]
            else:
                cmd = ' '.join(process.cmdline())
        except BaseException:
            cmd = 'Unknown'

        try:
            name = process.name()
        except BaseException:
            name = 'Unknown'

        try:
            exe = process.exe()
        except BaseException:
            exe = 'Unknown'

        try:
            username = process.username()
        except BaseException:
            username = 'Unknown'

        try:
            # Check if process pid is in ps_procs
            if pid in ps_procs:
                proc = ps_procs.get(pid)
                cpu_percent = round(float(proc[0]), 2)
            else:
                cpu_percent = round(process.cpu_percent(sleep) / psutil.cpu_count(), 2)
        except BaseException:
            cpu_percent = 0

        try:
            # Check if process pid is in ps_procs
            if pid in ps_procs:
                proc = ps_procs.get(pid)
                mem_percent = round(float(proc[1]), 2)
            else:
                mem_percent = round(process.memory_percent(), 2)
        except BaseException:
            mem_percent = 0;

        try:
            # Make unit types
            u = 'B'
            if units != 'B':
                u = '%s%s' % (units, 'B')

            # Get adjusted scales
            pmi = process.memory_info()
            value, uts = self.adjust_scale(self, pmi.rss, units)
            mem_rss = (value, u)
            value, uts = self.adjust_scale(self, pmi.vms, units)
            mem_vms = (value, u)
        except Exception as exc:
            #logging.exception(exc)
            mem_rss, mem_vms = (0, 'B'), (0, 'B')

        return {'pid': int(pid),
                'name': name,
                'exe': exe,
                'cmd': cmd,
                'username': username,
                'cpu_percent': (cpu_percent, '%'),
                'mem_percent': (mem_percent, '%'),
                'mem_rss': mem_rss,
                'mem_vms': mem_vms}

    def get_process_dict(self, *args, **kwargs):
        units = kwargs.get('units', ['B'])
        sleep = self.get_sleep(kwargs)
        proc_filter = self.make_filter(*args, **kwargs)
        processes = []
        ps_procs = {}

        # Mac OS X requires using ps command to get cpu/memory data (as nagios)
        uname = platform.uname()[0]
        if uname == 'Darwin':
            ps_out = tempfile.TemporaryFile()
            procs = subprocess.Popen(['ps', 'aux'], stdout=ps_out)
            procs.wait()
            ps_out.seek(0)
            
            # The first line is the header
            ps_out.readline()

            # Loop through each line and get data on procs then find the matching
            # proc in the psutils data and give the cpu/memory usage to it
            for line in ps_out.readlines():
                cols = line.split()
                ps_procs[cols[1]] = [cols[2], cols[3]]

        # AIX requires special ps calls to get full cmd line info
        elif uname == "AIX":
            ps_out = tempfile.TemporaryFile()
            procs = subprocess.Popen(['ps', 'auxwww'], stdout=ps_out)
            procs.wait()
            ps_out.seek(0)
            ps_out.readline() # Read first line (header)

            # Loop through each line and grab the proc information from ps auxwww
            # so that we get the proper command line arguments on AIX (psutil problem)
            for line in ps_out.readlines():
                cols = line.split()
                ps_procs[cols[1]] = [cols[2], cols[3], ' '.join(cols[10:])]

        # Do actual process looping
        for process in psutil.process_iter():
            try:
                proc_obj = self.standard_form(self, process, ps_procs, units[0], sleep)
                if proc_filter(proc_obj):
                    processes.append(proc_obj)
            except Exception as e:
                # Could not access process, most likely because of windows permissions
                logging.exception(e)
                continue

        return processes

    def walk(self, *args, **kwargs):
        self.method = self.get_process_dict
        if kwargs.get('first', True):
            return {self.name: self.method(*args, **kwargs)}
        else:
            return {self.name: []}

    def get_process_label(self, request_args):
        title = 'Process count'

        exes = self.get_exe(request_args)
        names = self.get_name(request_args)
        cpu_percent = self.get_cpu_percent(request_args)
        mem_percent = self.get_mem_percent(request_args)

        if self.get_combiner(request_args) == all:
            combiner = 'and'
        else:
            combiner = 'or'

        if exes or names or cpu_percent or mem_percent:
            title += ' for'
            if exes:
                title += ' exes named '
                title += ','.join(exes)
                if names or cpu_percent or mem_percent:
                    title += ' ' + combiner
            if names:
                title += ' processes named '
                title += ','.join(names)
                if cpu_percent or mem_percent:
                    title += ' ' + combiner
            if cpu_percent:
                title += ' CPU usage greater than %.2f' % cpu_percent
                if mem_percent:
                    title += ' ' + combiner
            if mem_percent:
                title += ' Memory Usage greater than %.2f' % mem_percent
        return [title]

    def run_check(self, *args, **kwargs):
        procs = self.walk(first=True, *args, **kwargs)

        def process_check_method():
            count = len(procs['processes'])
            return [count, '']

        self.method = process_check_method

        if kwargs.get('perfdata_label', None) is None:
            kwargs['perfdata_label'] = ['process_count']

        if kwargs.get('title', None) is None:
            kwargs['title'] = self.get_process_label(kwargs)

        check_return = super(ProcessNode, self).run_check(*args, **kwargs)

        # Add the process information, one process per line, to long output
        proc_count = len(procs['processes'])
        if proc_count > 0:
            tmem = 0
            tcpu = 0
            tmem_vms = 0
            tmem_rss = 0
            mem_unit = ''

            # Generate long output for service
            extra = '\nProcesses Matched\nPID: Name: Username: Exe: Memory: CPU\n-----------------------------------\n'
            for proc in procs['processes']:
                tmem += proc['mem_percent'][0]
                tcpu += proc['cpu_percent'][0]
                tmem_vms += proc['mem_vms'][0]
                tmem_rss += proc['mem_rss'][0]
                mem_unit = proc['mem_vms'][1]
                memory = '%s %s (VMS %.2f %s, RSS %.2f %s)' % (proc['mem_percent'][0], '%', proc['mem_vms'][0],
                    proc['mem_vms'][1], proc['mem_rss'][0], proc['mem_rss'][1])
                extra += '%s: %s: %s: %s: %.2f %s\n' % (proc['pid'], proc['name'], proc['username'],
                    memory, proc['cpu_percent'][0], '%')
            
            # Add totals to the output
            extra += '\nTotal Memory: %.2f %s (VMS %.2f %s, RSS %.2f %s)\n' % (tmem, '%', tmem_vms, mem_unit, tmem_rss, mem_unit)
            extra += 'Total CPU: %.2f %s\n' % (tcpu, '%')

            # Add totals to perfdata
            extra_perfdata = " 'cpu'=%s%s;;; 'memory'=%s%s;;; 'memory_vms'=%s%s;;; 'memory_rss'=%s%s;;;" % (tcpu, '%',
                tmem, '%', tmem_vms, mem_unit, tmem_rss, mem_unit)

            check_return['stdout'] += extra_perfdata + extra

        return check_return


def get_node():
    return ProcessNode('processes', None)
