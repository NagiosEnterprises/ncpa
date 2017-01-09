#!/usr/bin/env python

# This script sets up cx_Freeze and bundles/freezes the entire program. We
# don't really care what OS we are on anymore, so it's the same no matter
# what you are working on.
#
# Example: python setup.py

import sys
import shutil
import os
import platform
from cx_Freeze import setup, Executable


# Defined constants
__ARCH__ = platform.architecture()[0].lower()
__SYSTEM__ = os.name


# Get version from the VERSION file and remove anything after the . such as
# 2.0.0.a or 3.0.0.rc1 to form a generic version number since we can't handle
# a version number like that on Windows
version_file = os.path.join(os.path.dirname(__file__), '..', 'VERSION')
version = open(version_file, 'r').readline().strip()

if not version[-1].isdigit():
    x = version.rsplit('.', 1)
    version = x[0]


# Files to be included in the package
packages = []
includes = ['passive', 'listener', 'ncpa']
excludes = ['Tkinter', 'tkinter', 'unittest']
bin_includes = []
include_files = [('var/log/ncpa.log', 'var/log/ncpa.log'),
                 ('listener/templates', 'listener/templates'),
                 ('listener/static', 'listener/static'),
                 ('build_resources/LicenseAgreement.txt', 'build_resources/LicenseAgreement.txt'),
                 'etc',
                 'plugins']


# Specific build options for Windows
if __SYSTEM__ == 'nt':

    include_files += [('build_resources/nsis_listener_options.ini', 'build_resources/nsis_listener_options.ini'),
                     ('build_resources/nsis_passive_options.ini', 'build_resources/nsis_passive_options.ini'),
                     ('build_resources/nsis_passive_checks.ini', 'build_resources/nsis_passive_checks.ini'),
                     ('build_resources/ncpa.ico', 'build_resources/ncpa.ico'),
                     ('build_resources/nagios_installer.bmp', 'build_resources/nagios_installer.bmp'),
                     ('build_resources/nagios_installer_logo.bmp', 'build_resources/nagios_installer_logo.bmp')]

    includes += ['cx_Logging', 'jinja2.ext']
    packages += ['idna']

    # Since in Python 3.5 cx_Freeze does not include sqlite3 by default we need to add this
    include_files += [os.path.join(sys.base_prefix, 'DLLs', 'sqlite3.dll')]

    binary = Executable("setup_config.py",
                        base="Win32Service",
                        targetName="ncpa.exe",
                        icon="build_resources/ncpa.ico")

# Specific build settings for Linux / Max OS X
elif __SYSTEM__ == 'posix':

    include_files += [('build_resources/ncpa.plist', 'build_resources/ncpa.plist'),
                      ('build_resources/macosinstall.sh', 'build_resources/macosinstall.sh'),
                      ('build_resources/ncpa_init', 'build_resources/ncpa_init')]

    bin_includes += ['libffi.so']

    binary = Executable("ncpa.py", base=None)


# Apply build options
buildOptions = dict(includes=includes,
                    excludes=excludes,
                    include_files=include_files,
                    packages=packages,
                    bin_includes=bin_includes,
                    zip_include_packages=["*"],
                    zip_exclude_packages=[])


# Create setup for distutils
setup(name = "NCPA",
      version = version,
      description = "Nagios Cross-Platform Agent",
      executables = [binary],
      options = dict(build_exe = buildOptions)
)


# Grab the proper files if we are on Windows 32bit or 64bit - Linux doesn't care
if __ARCH__ == '32bit':
    os.rename(os.path.join('build', 'exe.win32-3.5'), os.path.join('build', 'NCPA'))
elif __ARCH__ == '64bit':
    os.rename(os.path.join('build', 'exe.win-amd64-3.5'), os.path.join('build', 'NCPA'))
else:
    print("unhandled architecture")
    sys.exit(1)


# Copy over the nsis file for building the installer if we are on Windows
if __SYSTEM__ == 'nt':
    shutil.copy('build_resources/ncpa.nsi', 'build/')
