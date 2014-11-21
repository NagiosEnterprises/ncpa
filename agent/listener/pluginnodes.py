import os
import logging
import nodes
import ConfigParser
import subprocess
import shlex
import re
import copy


class PluginNode(nodes.RunnableNode):

    def __init__(self, plugin, plugin_abs_path, *args, **kwargs):
        self.name = plugin
        self.plugin_abs_path = plugin_abs_path
        self.arguments = []

    def accessor(self, path, config):
        self.arguments = path
        return copy.deepcopy(self)

    def walk(self, config, **kwargs):
        result = self.execute_plugin(config)
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

    def execute_plugin(self, config, *args, **kwargs):
        """Runs custom scripts that MUST be located in the scripts subdirectory
        of the executable

        """
        #Get any special instructions from the config for executing the plugin
        instructions = self.get_plugin_instructions(config)

        #Make our command line
        cmd = self.get_cmdline(instructions)
        logging.debug('Running process with command line: `%s`', ' '.join(cmd))

        running_check = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        running_check.wait()

        returncode = running_check.returncode
        stdout = ''.join(running_check.stdout.readlines()).replace('\r\n', '\n').replace('\r', '\n').strip()

        return {'returncode': returncode, 'stdout': stdout}

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
                plugin_abs_path = os.path.join(plugin_path, plugin)
                if os.path.isfile(plugin_abs_path):
                    self.children[plugin] = PluginNode(plugin, plugin_abs_path)
        except OSError as exc:
            logging.warning('Unable to access directory %s', plugin_path)
            logging.warning('Unable to assemble plugins. Does the directory exist? - %r', exc)

    def accessor(self, path, config):
        self.setup_plugin_children(config)
        return super(PluginAgentNode, self).accessor(path, config)

    def walk(self, *args, **kwargs):
        self.setup_plugin_children(kwargs['config'])
        return {self.name: self.children.keys()}
