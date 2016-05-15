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
import platform

version_file = os.path.join(os.path.dirname(__file__),
                            '..',
                            'VERSION')
version = open(version_file, 'r').readline().strip()

sys.argv += ['-p', 'xml']

includefiles = [('var/ncpa_listener.log', 'var/ncpa_listener.log'),
                ('var/ncpa_passive.log', 'var/ncpa_passive.log'),
                ('etc/ncpa.cfg', 'etc/ncpa.cfg'),
                'plugins',
                ('listener/templates', 'listener/templates'),
                ('listener/static', 'listener/static'),
                'passive']

includes = ['xml.dom.minidom']
                    
includefiles += [('build_resources/LicenseAgreement.txt', 'build_resources/LicenseAgreement.txt'),
                 ('build_resources/quickstart.ini', 'build_resources/quickstart.ini'),
                 ('build_resources/ncpa.ico', 'build_resources/ncpa.ico')]
				 
buildOptions = dict(includes=includes + ["ncpa_windows"],
                    include_files=includefiles)

listener = Executable("ncpa_windows_listener.py", 
                      base = "Win32Service",
                      targetName="ncpa_listener.exe")

passive = Executable("ncpa_windows_passive.py",
                     base = "Win32Service",
                     targetName = "ncpa_passive.exe")

setup(name="NCPA",
	  version=version,
      description="Nagios Cross Platform Agent Installer",
      executables=[listener, passive],
      options=dict(build_exe=buildOptions),
)

if platform.architecture()[0].lower() == '32bit':
    os.rename(os.path.join('build', 'exe.win32-2.7'), os.path.join('build', 'NCPA'))
elif platform.architecture()[0].lower() == '64bit':
    os.rename(os.path.join('build', 'exe.win-amd64-2.7'), os.path.join('build', 'NCPA'))
else:
    print "unhandled architecture"
    sys.exit(1)

shutil.copy(u'build_resources/ncpa.nsi', u'build/')
