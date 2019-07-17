#
# A simple setup script for creating a POSIX service.
#

import sys
import shutil
from cx_Freeze import setup, Executable
import os
import tarfile
import site

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
excludes = ['Tkinter','tkinter','collections.sys','collections._weakref']
packages = []

# Shared library include overrides
bin_includes = ['libssl.so', 'libcrypto.so', 'libffi.so']

# Special includes for AIX systems
if 'aix' in sys.platform:
    include_files += [('/opt/freeware/lib/libpython2.7.so', 'libpython2.7.so'),
                      ('/opt/freeware/lib/libncurses.so', 'libncurses.so'),
                      ('/opt/freeware/lib/libz.a', 'libz.a'),
                      ('/usr/lib/libsqlite3.so', 'libsqlite3.so'),
                      ('/usr/lib/libssl.a', 'libssl.a'),
                      ('/usr/lib/libcrypto.a', 'libcrypto.a'),
                      ('/usr/lib/libffi.a', 'libffi.a'),
                      ('/opt/freeware/lib/libgcc_s.a', 'libgcc_s.a'),
                      ('/opt/freeware/lib/libssl.so', 'libssl.so'),
                      ('/opt/freeware/lib/libcrypto.so', 'libcrypto.so')]

# For new cffi and cryptography
try:
    cffi_backend = os.path.join(site.getsitepackages()[0], '.libs_cffi_backend')
    if os.path.isdir(cffi_backend):
        for f in os.listdir(cffi_backend):
            include_files += [(os.path.join(cffi_backend, f), os.path.join('.libs_cffi_backend', f))]
except AttributeError as ex:
    pass

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
