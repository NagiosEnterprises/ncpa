# A simple setup script for creating a Windows service. See the comments in the
# Config.py and ServiceHandler.py files for more information on how to set this
# up.
#
# Installing the service is done with the option --install <Name> and
# uninstalling the service is done with the option --uninstall <Name>. The
# value for <Name> is intended to differentiate between different invocations
# of the same service code -- for example for accessing different databases or
# using different configuration files.

import sys
import shutil
from cx_Freeze import setup, Executable
import os
import tarfile

shutil.rmtree('build', ignore_errors=True)

includefiles = ['var/ncpa_listener.log', 
                'var/ncpa_passive.log',
                'etc/ncpa.cfg',
                'plugins',
                'listener/templates',
                'listener/static']

# It does not appear the cx_Freeze honors the package directive
includes = ['xml.dom.minidom', 
            'OpenSSL',
            'jinja2.ext']

excludes = ['Tkinter',
            'tkinter']

packages = []

includefiles += ['build_resources/NagiosSoftwareLicense.txt',
                 'build_resources/ncpa_listener.plist',
                 'build_resources/ncpa_passive.plist',
                 'build_resources/macosinstall.sh',
                 'build_resources/listener_init',
                 'build_resources/passive_init']

buildOptions = dict(includes=includes,
                    include_files=includefiles,
                    packages=packages)

base = None

setup(name = "NCPA",
      version = "1.5",
      description = "NCPA",
      options = dict(build_exe=buildOptions),
      executables = [Executable("ncpa_posix_listener.py", base=base), 
                     Executable("ncpa_posix_passive.py", base=base)])

