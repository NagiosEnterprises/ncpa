#
# A simple setup script for creating a POSIX service.
#

import sys
import shutil
from cx_Freeze import setup, Executable
import os
import tarfile

version_file = os.path.join(os.path.dirname(__file__),
                            '..',
                            'VERSION')
version = open(version_file, 'r').readline().strip()

shutil.rmtree('build', ignore_errors=True)

include_files = [('var/log/ncpa_listener.log', 'var/log/ncpa_listener.log'),
                 ('var/log/ncpa_passive.log', 'var/log/ncpa_passive.log'),
                 'etc',
                 'plugins',
                 ('listener/templates', 'listener/templates'),
                 ('listener/static', 'listener/static')]

# It does not appear the cx_Freeze honors the package directive
includes = ['xml.dom.minidom','jinja2.ext','passive']
excludes = ['Tkinter','tkinter']
packages = []

# Shared library include overrides
bin_includes = ['libffi.so', 'libssl.so', 'libcrypto.so']

# For new cffi and cryptography
cffi_backend = os.path.join('/usr/lib64/python2.7/site-packages', '.libs_cffi_backend')
if os.path.isdir(cffi_backend):
    include_files += [(cffi_backend, '.libs_cffi_backend')]

# Special includes for AIX systems
if 'aix' in sys.platform:
    include_files += [('/opt/freeware/lib/libpython2.7.so', 'libpython2.7.so'),
                      ('/usr/lib/libsqlite3.a', 'libsqlite3.a'),
                      ('/usr/lib/libssl.so', 'libssl.so'),
                      ('/usr/lib/libcrypto.so', 'libcrypto.so'),
                      ('/usr/lib/libcrypto.a', 'libcrypto.a'),
                      ('/usr/lib/libffi.a', 'libffi.a'),
                      ('/opt/freeware/lib/libgcc_s.a', 'libgcc_s.a')]

include_files += [('build_resources/LicenseAgreement.txt', 'build_resources/LicenseAgreement.txt'),
                  ('build_resources/ncpa_listener.plist', 'build_resources/ncpa_listener.plist'),
                  ('build_resources/ncpa_passive.plist', 'build_resources/ncpa_passive.plist'),
                  ('build_resources/macosinstall.sh', 'build_resources/macosinstall.sh'),
                  ('build_resources/macosuninstall.sh', 'build_resources/macosuninstall.sh'),
                  ('build_resources/listener_init', 'build_resources/listener_init'),
                  ('build_resources/passive_init', 'build_resources/passive_init')]

buildoptions = dict(includes=includes,
                    include_files=include_files,
                    excludes=excludes,
                    packages=packages,
                    bin_includes=bin_includes)

# Build the actual binaries and bundle files

base = None
setup(name = "NCPA",
      version = version,
      description = "NCPA",
      options = dict(build_exe=buildoptions),
      executables = [Executable("ncpa_listener.py", base=base),
                     Executable("ncpa_passive.py", base=base)])
