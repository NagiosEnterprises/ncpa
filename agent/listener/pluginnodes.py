import os
import time
import logging
import subprocess
import shlex
import re
import copy
import queue
import listener.nodes as nodes
import listener.database as database
import listener.server
from threading import Timer


# Windows does not have the pwd and grp module and does not need it since only Unix
# uses these modules to change permissions.
try:
    import pwd
    import grp
except ImportError:
    pass


class PluginNode(nodes.RunnableNode):

    def __init__(self, plugin, plugin_abs_path, *args, **kwargs):
        self.name = plugin
        self.plugin_abs_path = plugin_abs_path
        self.arguments = []

    def accessor(self, path, config, full_path):
        self.arguments = path
        return copy.deepcopy(self)

    def walk(self, config, **kwargs):
        result = self.execute_plugin(config, **kwargs)
        return result

    def get_plugin_instructions(self, config):
        """Returns the instruction to use for the given plugin.
        If nothing exists for the suffix, then simply return the basic

        $plugin_name $plugin_args   

        """
        _, extension = os.path.splitext(self.name)
        try:
            return config.get('plugin directives', extension)
        except Exception:
            return '$plugin_name $plugin_args'

    def kill_proc(self, p, t, q):
        p.kill()
        q.put("Error: Plugin command timed out. (%d sec)" % t)

    def execute_plugin(self, config, *args, **kwargs):
        """Runs custom scripts that MUST be located in the scripts subdirectory
        of the executable

        """
        # Get any special instructions from the config for executing the plugin
        instructions = self.get_plugin_instructions(config)

        # Get user and group from config file
        #user_uid = config.get('listener', 'uid', 'nagios')
        #user_gid = config.get('listener', 'gid', 'nagios')

        # Get plugin command timeout value, if it exists
        try:
            timeout = int(config.get('plugin directives', 'plugin_timeout'))
        except Exception as e:
            timeout = 60

        # Get the check logging value
        try:
            check_logging = int(config.get('general', 'check_logging'))
        except Exception as e:
            check_logging = 1

        # Make our command line
        cmd = self.get_cmdline(instructions)
        logging.debug('Running process with command line: `%s`', ' '.join(cmd))

        # Run a command and wait for return
        run_time_start = time.time()
        running_check = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         universal_newlines=True)

        try:
            stdout, stderr = running_check.communicate(timeout=timeout)
        except TimeoutExpired:
            running_check.kill()
            stdout, stderr = running_check.communicate()

        run_time_end = time.time()
        returncode = running_check.returncode

        # Pull from the queue if we have a error and the stdout is empty
        if returncode == 1 and not stdout:
            if q.qsize() > 0:
                stdout = q.get()

        cleaned_stdout = ''.join(stdout).strip()

        if not listener.server.__INTERNAL__ and check_logging == 1:
            db = database.DB()
            dbc = db.get_cursor()
            data = (kwargs['accessor'].rstrip('/'), run_time_start, run_time_end, returncode,
                    cleaned_stdout, kwargs['remote_addr'], 'Active')
            dbc.execute('INSERT INTO checks VALUES (?, ?, ?, ?, ?, ?, ?)', data)
            db.commit()

        return {'returncode': returncode, 'stdout': cleaned_stdout}

    @staticmethod
    def demote(user_uid, user_gid):
        def result():

            # Grab the uid if it's not specifically defined
            uid = user_uid
            if not isinstance(user_uid, int):
                if not user_uid.isdigit():
                    u = pwd.getpwnam(user_uid)
                    uid = u.pw_uid
                else:
                    uid = int(user_uid)

            # Grab the gid if not specifically defined
            gid = user_gid
            if not isinstance(user_gid, int):
                if not user_gid.isdigit():
                    g = grp.getgrnam(user_gid)
                    gid = g.gr_gid
                else:
                    gid = int(user_gid)

            # Set the actual uid and gid
            os.setgid(gid)
            os.setuid(uid)
        return result

    def get_cmdline(self, instruction):
        """Execute with special instructions.

        EXAMPLE instruction (Powershell):
        powershell -ExecutionPolicy Unrestricted $plugin_name $plugin_args

        EXAMPLE instruction (VBS):
        wscript $plugin_name $plugin_args

        """
        command = []
        
        lexer = shlex.shlex(instruction)
        lexer.whitespace_split = True
        
        for x in lexer:
            if '$plugin_name' in x:
                replaced = x.replace('$plugin_name', self.plugin_abs_path)
                command.append(replaced)
            elif '$plugin_args' == x:
                if self.arguments:
                    for y in self.arguments:
                        command.append(y)
            else:
                command.append(x)
        return command


class PluginAgentNode(nodes.ParentNode):

    def __init__(self, name, *args, **kwargs):
        self.name = name

    def setup_plugin_children(self, config):
        plugin_path = config.get('plugin directives', 'plugin_path')
        self.children = {}

        try:
            plugins = os.listdir(plugin_path)
            for plugin in plugins:
                if plugin == '.keep':
                    continue
                plugin_abs_path = os.path.join(plugin_path, plugin)
                if os.path.isfile(plugin_abs_path):
                    self.children[plugin] = PluginNode(plugin, plugin_abs_path)
        except OSError as exc:
            logging.warning('Unable to access directory %s', plugin_path)
            logging.warning('Unable to assemble plugins. Does the directory exist? - %r', exc)

    def accessor(self, path, config, full_path):
        self.setup_plugin_children(config)
        return super(PluginAgentNode, self).accessor(path, config, full_path)

    def walk(self, *args, **kwargs):
        self.setup_plugin_children(kwargs['config'])
        return { self.name: list(self.children.keys()) }
