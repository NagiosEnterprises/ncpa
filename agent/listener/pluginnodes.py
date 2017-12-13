# -*- coding: utf-8 -*-

import os
import time
import logging
import nodes
import ConfigParser
import subprocess
import shlex
import re
import copy
import Queue
import environment
import database
import server
from threading import Timer

# Windows does not have the pwd and grp module and does not need it since only Unix
# uses these modules to change permissions.
try:
    import pwd
except ImportError:
    pass

try:
    import grp
except ImportError:
    pass

class PluginNode(nodes.RunnableNode):

    def __init__(self, plugin, plugin_abs_path, *args, **kwargs):
        self.name = plugin
        self.plugin_abs_path = plugin_abs_path
        self.arguments = []

    def accessor(self, path, config, full_path, args):

        # Get raw args value(s) and check if we need to add them
        raw_args = args.getlist('args')
        if len(raw_args) > 0:
            self.arguments += raw_args

        # Add arguments that may have been passed with the path
        # THIS IS TO KEEP OLD VERSION < 2.1 FUNCTIONALITY
        #  ** this will be deprecated in NCPA 3 ***
        if len(path) > 0:
            self.arguments += path

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
        except ConfigParser.NoOptionError:
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

        # Create a list of plugin names that should be ran as sudo
        sudo_plugins = []
        try:
            run_with_sudo = config.get('plugin directives', 'run_with_sudo')
            sudo_plugins = [x.strip() for x in run_with_sudo.split(',')]
        except Exception as e:
            pass

        # Make our command line
        cmd = self.get_cmdline(instructions, sudo_plugins)
        logging.debug('Running process with command line: `%s`', ' '.join(cmd))

        # Run the command in a new subprocess
        run_time_start = time.time()
        running_check = subprocess.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        queue = Queue.Queue(maxsize=2)
        timer = Timer(timeout, self.kill_proc, [running_check, timeout, queue])

        try:
            timer.start()
            stdout, stderr = running_check.communicate()
        finally:
            timer.cancel()

        run_time_end = time.time()
        returncode = running_check.returncode

        # Pull from the queue if we have a error and the stdout is empty
        if returncode == 1 and not stdout:
            if queue.qsize() > 0:
                stdout = queue.get()

        cleaned_stdout = unicode(''.join(stdout.decode("utf-8", "ignore")).replace('\r\n', '\n').replace('\r', '\n').strip())

        if not server.__INTERNAL__ and check_logging == 1:
            db = database.DB()
            db.add_check(kwargs['accessor'].rstrip('/'), run_time_start, run_time_end, returncode,
                         cleaned_stdout, kwargs['remote_addr'], 'Active')

        output = { 'returncode': returncode, 'stdout': cleaned_stdout }

        # If debug=1 or true then show the command we ran
        if kwargs['debug']:
            output['cmd'] = ' '.join(cmd)

        return output

    def get_cmdline(self, instruction, sudo_plugins):
        """Execute with special instructions.

        EXAMPLE instruction (Powershell):
        powershell -ExecutionPolicy Unrestricted $plugin_name $plugin_args

        EXAMPLE instruction (VBS):
        wscript $plugin_name $plugin_args

        """
        command = []

        # Add sudo for commands that need to run as sudo
        if os.name == 'posix':
            if self.name in sudo_plugins:
                command.append('sudo')

        # Set shlex to use posix mode on posix machines (so that we can pass something like
        # --metric='disk/logical/|' and have it properly format quotes)
        mode = False
        if os.name == 'posix':
            mode = True
        
        lexer = shlex.shlex(instruction, posix=mode)
        lexer.whitespace_split = True

        for x in lexer:
            if '$plugin_name' in x:
                replaced = x.replace('$plugin_name', self.plugin_abs_path)
                command.append(replaced)
            elif '$plugin_args' == x:
                if self.arguments:
                    args = shlex.shlex(' '.join(self.arguments), posix=mode)
                    args.whitespace_split = True
                    for a in args:
                        command.append(a)
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

    def accessor(self, path, config, full_path, args):
        self.setup_plugin_children(config)
        return super(PluginAgentNode, self).accessor(path, config, full_path, args)

    def walk(self, *args, **kwargs):
        self.setup_plugin_children(kwargs['config'])
        plugins = list(self.children.keys())
        plugins.sort()
        return { self.name: plugins }
