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
bin_includes = []

# Special includes for AIX systems
if 'aix' in sys.platform:
    include_files += [('/opt/freeware/lib/python2.7/config/libpython2.7.so', 'libpython2.7.so'),
                      ('/opt/freeware/lib/libsqlite3.a', 'libsqlite3.a'),
                      ('/opt/freeware/lib/libssl.so', 'libssl.so'),
                      ('/opt/freeware/lib/libcrypto.so', 'libcrypto.so'),
                      ('/opt/freeware/lib/libffi.so', 'libffi.so')]

include_files += [('build_resources/LicenseAgreement.txt', 'build_resources/LicenseAgreement.txt'),
                  ('build_resources/ncpa_listener.plist', 'build_resources/ncpa_listener.plist'),
                  ('build_resources/ncpa_passive.plist', 'build_resources/ncpa_passive.plist'),
                  ('build_resources/macosinstall.sh', 'build_resources/macosinstall.sh'),
                  ('build_resources/listener_init', 'build_resources/listener_init'),
                  ('build_resources/passive_init', 'build_resources/passive_init')]

buildoptions = dict(includes=includes,
                    include_files=include_files,
                    excludes=excludes,
                    packages=packages,
                    bin_includes=bin_includes)

base = None

setup(name = "NCPA",
      version = version,
      description = "NCPA",
      options = dict(build_exe=buildoptions),
      executables = [Executable("ncpa_listener.py", base=base),
                     Executable("ncpa_passive.py", base=base)])
