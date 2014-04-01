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

shutil.rmtree(u'build', ignore_errors=True)

sys.argv += [u'-p', u'xml']

includefiles = [u'var/ncpa_listener.log', 
                u'var/ncpa_passive.log',
                u'etc/ncpa.cfg',
                u'plugins',
                u'listener/templates',
                u'listener/static']

# It does not appear the cx_Freeze honors the package directive
includes = [u'xml.dom.minidom', 
            u'OpenSSL',
            u'jinja2.ext',
            ]

packages = []

includefiles += [u'build_resources/NagiosSoftwareLicense.txt',
                 u'build_resources/listener_init',
                 u'build_resources/passive_init']

buildOptions = dict(includes=includes,
                    include_files=includefiles,
                    packages=packages)

base = None

setup(name = u"NCPA",
      version = u"1.4",
      description = u"NCPA",
      options = dict(build_exe=buildOptions),
      executables = [Executable(u"ncpa_posix_listener.py", base=base), 
                     Executable(u"ncpa_posix_passive.py", base=base)])

