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

sys.argv += ['-p', 'xml']

includefiles = [    'var/ncpa_listener.log', 
                    'var/ncpa_passive.log',
                    'etc/ncpa.cfg',
                    'plugins',
                    'listener/templates',
                    'listener/static',
                    'passive'
                    ]

includes = ['xml.dom.minidom']
                    
includefiles += [   'build_resources/NagiosSoftwareLicense.txt',
                    'build_resources/listener_init',
                    'build_resources/passive_init'
                ]

buildOptions = dict( includes = includes,
                         include_files = includefiles
)


#~ setup(
    #~ name = "NCPA",
    #~ version = "0.3",
    #~ description = "Nagios Cross Platform Agent Installer",
    #~ executables = [listener, passive],
    #~ options = dict(build_exe = buildOptions),
#~ )


# GUI applications require a different base on Windows (the default is for a
# console application).
base = None

setup(  name = "NCPA",
        version = "0.3",
        description = "NCPA",
        options = dict(build_exe = buildOptions),
        executables = [ Executable("ncpa_posix_listener.py", base=base), 
                        Executable("ncpa_posix_passive.py", base=base)
                    ]
)

os.chdir('build/')
os.rename('exe.linux-i686-2.6', 'ncpa-1.0')

tar = tarfile.open('ncpa-1.0.tar.gz', 'w:gz')
tar.add('ncpa-1.0')
tar.close()

for dir in ['BUILD', 'RPMS', 'SOURCES', 'SPECS', 'SRPMS']:
    os.makedirs(dir)

shutil.copy('ncpa-1.0.tar.gz', 'SOURCES/')
shutil.copy('../build_resources/ncpa.spec', 'SPECS/')

os.system('rpmbuild -ba SPECS/ncpa.spec')
