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
                    'listener/static'
                    ]

if 'bdist_msi' in sys.argv:
    includefiles = [ 'Config.py', 'start.bat' ]
    buildOptions = dict(includes = ["ncpa_cx_windows"],
                        include_files = includefiles)
    executable = Executable("Config.py", 
                            base = "Win32Service",
                            targetName = "ncpa_cx_windows.exe"
                )

setup(
        name = "NCPAListener",
        version = "0.2",
        description = "NCPA Listening Daemon",
        executables = [executable],
        options = dict(build_exe = buildOptions),
)

