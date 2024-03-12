#!/usr/bin/env python

"""
cx_Freeze setup script for NCPA

This script sets up cx_Freeze and bundles/freezes the entire program. We
don't really care what OS we are on anymore, so it's the same no matter
what you are working on.

Example: python setup.py build_exe
    [python interpreter] [cx_Freeze setup script] [build command]
"""

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

print("***** Freezing: ", __ARCH__, __SYSTEM__, version)

if not version[-1].isdigit():
    x = version.rsplit('.', 1)
    version = x[0]


# Files to be included in the package
packages = ['idna', 'passive', 'listener', 'gevent', 'asyncio']
includes = ['ncpa', 'jinja2.ext']
excludes = ['Tkinter', 'tkinter', 'unittest']
bin_includes = []

include_files = [('var/log/ncpa_listener.log'   , 'var/log/ncpa_listener.log'),
                 ('var/log/ncpa_passive.log'    , 'var/log/ncpa_passive.log'),
                 ('listener/templates'          , 'listener/templates'),
                 ('listener/static'             , 'listener/static'),
                 ('../build/resources/LicenseAgreement.txt', 'build_resources/LicenseAgreement.txt'),
                 'etc',
                 'plugins']

# Build settings - Windows
if __SYSTEM__ == 'nt':

    include_files += [('../build/resources/nsis_listener_options.ini'   , 'build_resources/nsis_listener_options.ini'),
                     ('../build/resources/nsis_passive_options.ini'     , 'build_resources/nsis_passive_options.ini'),
                     ('../build/resources/nsis_passive_checks.ini'      , 'build_resources/nsis_passive_checks.ini'),
                     ('../build/resources/ncpa.ico'                     , 'build_resources/ncpa.ico'),
                     ('../build/resources/nagios_installer.bmp'         , 'build_resources/nagios_installer.bmp'),
                     ('../build/resources/nagios_installer_logo.bmp'    , 'build_resources/nagios_installer_logo.bmp'),
                     ('../build/resources/ncpa.nsi'                     , 'build_resources/ncpa.nsi'),
                     (sys.executable                                    , 'python.exe')]

    # include pywin32 modules
    packages += ['win32serviceutil', 'win32service', 'win32event', 'servicemanager', 'win32timezone']

    ### build as a windows executable -- NSIS will install it as a service
    binary = Executable(script='ncpa.py',
                        icon='../build/resources/ncpa.ico')
#

# Build settings - Linux / Max OS X
elif __SYSTEM__ == 'posix':

    include_files += [('../startup/default-plist'   , 'build_resources/default-plist'),
                      ('../startup/default-init'    , 'build_resources/default-init'),
                      ('../startup/default-service' , 'build_resources/default-service'),
                      (os.path.join(sys.executable) , 'python')]

    # Shared library include overrides
    bin_includes += ['libffi.so', 'libssl.so.3', 'libcrypto.so.3']

    # Special includes for Mac OS
    if 'darwin' in sys.platform:
        include_files += [('../build/resources/macosinstall.sh'  , 'build_resources/macosinstall.sh'),
                         ('../build/resources/macosuninstall.sh', 'build_resources/macosuninstall.sh'),
                         ('../build/resources/macosreadme.txt', 'build_resources/macosreadme.txt'),
                         ('/usr/local/opt/mpdecimal/lib/libmpdec.4.0.0.dylib', 'lib/libmpdec.4.0.0.dylib'),
                         ('/usr/local/opt/openssl@3/lib/libcrypto.3.dylib', 'lib/libcrypto.3.dylib'),
                         ('/usr/local/opt/openssl@3/lib/libssl.3.dylib', 'lib/libssl.3.dylib'),
                         ('/usr/local/opt/sqlite/lib/libsqlite3.0.dylib', 'lib/libsqlite3.0.dylib'),
                         ('/usr/local/opt/xz/lib/liblzma.5.dylib', 'lib/liblzma.5.dylib')]

        os_major_version = platform.mac_ver()[0].split('.')[:1][0]
        if os_major_version == '10':
            include_files += [('/usr/local/opt/libffi/lib/libffi.8.dylib', 'lib/libffi.8.dylib')]

    # Special includes for AIX systems
    if 'aix' in sys.platform:
        include_files += [('/opt/freeware/lib/libpython3.6.so'  , 'libpython3.6.so'),
                          ('/usr/lib/libsqlite3.a'              , 'libsqlite3.a'),
                          ('/usr/lib/libssl.so'                 , 'libssl.so'),
                          ('/usr/lib/libcrypto.so'              , 'libcrypto.so'),
                          ('/usr/lib/libcrypto.a'               , 'libcrypto.a'),
                          ('/usr/lib/libffi.a'                  , 'libffi.a'),
                          ('/opt/freeware/lib/libgcc_s.a'       , 'libgcc_s.a')]

    binary = Executable('ncpa.py', base=None)

# Apply build options
buildOptions = dict(includes=includes,
                    excludes=excludes,
                    include_files=include_files,
                    packages=packages,
                    bin_includes=bin_includes,
                    replace_paths=[('*', '')],
                    zip_include_packages=['*'],
                    zip_exclude_packages=[],
                    include_msvcr=True)

# Create setup for distutils
setup(name = "NCPA",
      version = version,
      description = "Nagios Cross-Platform Agent",
      executables = [binary],
      options = dict(build_exe = buildOptions)
)

if __SYSTEM__ == 'nt':
    # Rename to enable NSI to find stuff
    py_ver = platform.python_version()
    py_ver = '.'.join(py_ver.split('.')[:2])
    if platform.architecture()[0].lower() == '32bit':
        os.rename(os.path.join('build', 'exe.win32-'+py_ver), os.path.join('build', 'NCPA'))
    elif platform.architecture()[0].lower() == '64bit':
        os.rename(os.path.join('build', 'exe.win-amd64-'+py_ver), os.path.join('build', 'NCPA'))
    else:
        print("unhandled architecture")
        sys.exit(1)

    shutil.copy(os.path.join('build','NCPA','build_resources','ncpa.nsi'), 'build/')

