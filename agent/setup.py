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

shutil.rmtree(u'build', ignore_errors=True)

sys.argv += [u'-p', u'xml']

includefiles = [    u'var/ncpa_listener.log', 
                    u'var/ncpa_passive.log',
                    u'etc/ncpa.cfg',
                    u'plugins',
                    u'listener/templates',
                    u'listener/static',
                    u'passive'
                    ]

includes = [u'xml.dom.minidom']
                    
includefiles += [   u'build_resources/NagiosSoftwareLicense.txt', 
                    u'build_resources/quickstart.ini',
                    u'build_resources/basic.ini',
                    u'build_resources/pickpath.ini',
                    u'build_resources/ncpa.ico' ]

buildOptions = dict( includes = includes + [u"ncpa_windows"],
                         include_files = includefiles)

listener  = Executable(     u"ListenerConfig.py", 
                            base = u"Win32Service",
                            targetName = u"ncpa_listener.exe"
            )

passive   = Executable(     u"PassiveConfig.py",
                            base = u"Win32Service",
                            targetName = u"ncpa_passive.exe"
            )

setup(
    name = u"NCPA",
    version = u"0.3",
    description = u"Nagios Cross Platform Agent Installer",
    executables = [listener, passive],
    options = dict(build_exe = buildOptions),
)

os.rename(os.path.join(u'build', u'exe.win32-2.7'), os.path.join(u'build', u'NCPA'))
shutil.copy(u'build_resources/ncpa.nsi', u'build/')
