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
from cx_Freeze import setup, Executable

includefiles = [    'var/ncpa.log', 
                    'etc/ncpa.cfg',
                    'plugins',
                    'listener/templates',
                    'listener/static',
                    'passive'
                    ]

includes = [    'lxml.etree', 
                'lxml._elementpath' 
           ]
                    
if 'bdist_msi' in sys.argv:
    includefiles += [ 'install.bat', 'uninstall.bat' ]
    
    buildOptions = dict( includes = includes + ["ncpa_windows"],
                         include_files = includefiles)
     
    listener  = Executable( "ListenerConfig.py", 
                            base = "Win32Service",
                            targetName = "ncpa_listener.exe"
                )
    passive   = Executable( "PassiveConfig.py",
                            base = "Win32Service",
                            targetName = "ncpa_passive.exe"
                )

setup(
        name = "NCPA",
        version = "0.3",
        description = "Nagios Cross Platform Agent Installer",
        executables = [listener, passive],
        options = dict(build_exe = buildOptions),
)

