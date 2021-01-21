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
# 3.0.0.a or 3.1.0.rc1 to form a generic version number since we can't handle
# a version number like that on Windows
version_file = os.path.join(os.path.dirname(__file__), '..', 'VERSION')
version = open(version_file, 'r').readline().strip()

if not version[-1].isdigit():
    x = version.rsplit('.', 1)
    version = x[0]


# Files to be included in the package
packages = ['idna', 'passive', 'listener', 'gevent', 'asyncio']
includes = ['ncpa', 'jinja2.ext']
excludes = ['Tkinter', 'tkinter', 'unittest']
bin_includes = []
include_files = [('var/log/ncpa.log', 'var/log/ncpa.log'),
                 ('listener/templates', 'listener/templates'),
                 ('listener/static', 'listener/static'),
                 ('../build/resources/LicenseAgreement.txt', 'build_resources/LicenseAgreement.txt'),
                 'etc',
                 'plugins']


# Specific build options for Windows
if __SYSTEM__ == 'nt':

    include_files += [('../build/resources/nsis_listener_options.ini', 'build_resources/nsis_listener_options.ini'),
                     ('../build/resources/nsis_passive_options.ini', 'build_resources/nsis_passive_options.ini'),
                     ('../build/resources/nsis_passive_checks.ini', 'build_resources/nsis_passive_checks.ini'),
                     ('../build/resources/ncpa.ico', 'build_resources/ncpa.ico'),
                     ('../build/resources/nagios_installer.bmp', 'build_resources/nagios_installer.bmp'),
                     ('../build/resources/nagios_installer_logo.bmp', 'build_resources/nagios_installer_logo.bmp'),
                     (os.path.join(sys.executable), 'python.exe')]

    binary = Executable("setup_config.py",
                        base="Win32Service",
                        targetName="ncpa.exe",
                        icon="../build/resources/ncpa.ico")

# Specific build settings for Linux / Max OS X
elif __SYSTEM__ == 'posix':

    include_files += [('../startup/default-plist', 'build_resources/default-plist'),
                      ('../startup/default-init', 'build_resources/default-init'),
                      ('../startup/default-service', 'build_resources/default-service'),
                      (os.path.join(sys.executable), 'python')]

    # Shared library include overrides
    bin_includes += ['libffi.so', 'libssl.so', 'libcrypto.so']

    # Special includes for Mac OS X
    if 'darwin' in sys.platform:
       include_files += [('../build/resources/macosinstall.sh', 'build_resources/macosinstall.sh'),
                         ('../build/resources/macosuninstall.sh', 'build_resources/macosuninstall.sh')]

    # Special includes for AIX systems
    if 'aix' in sys.platform:
        include_files += [('/opt/freeware/lib/libpython3.6.so', 'libpython3.6.so'),
                          ('/usr/lib/libsqlite3.a', 'libsqlite3.a'),
                          ('/usr/lib/libssl.so', 'libssl.so'),
                          ('/usr/lib/libcrypto.so', 'libcrypto.so'),
                          ('/usr/lib/libcrypto.a', 'libcrypto.a'),
                          ('/usr/lib/libffi.a', 'libffi.a'),
                          ('/opt/freeware/lib/libgcc_s.a', 'libgcc_s.a')]

    binary = Executable('ncpa.py', base=None)


# Apply build options
buildOptions = dict(includes=includes,
                    excludes=excludes,
                    include_files=include_files,
                    packages=packages,
                    bin_includes=bin_includes,
                    replace_paths=[('*', '')],
                    zip_include_packages=['*'],
                    zip_exclude_packages=[])


# Create setup for distutils
setup(name = "NCPA",
      version = version,
      description = "Nagios Cross-Platform Agent",
      executables = [binary],
      options = dict(build_exe = buildOptions)
)

