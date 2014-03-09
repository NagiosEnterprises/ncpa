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

includefiles = ['var/ncpa_listener.log', 
                'var/ncpa_passive.log',
                'etc/ncpa.cfg',
                'plugins',
                'listener/templates',
                'listener/static',
                'passive']

# It does not appear the cx_Freeze honors the package directive
includes = ['xml.dom.minidom', 
            'OpenSSL',
            'jinja2.ext',
            'cryptography.hazmat.bindings.openssl.aes',
            'cryptography.hazmat.bindings.openssl.asn1',
            'cryptography.hazmat.bindings.openssl.bignum',
            'cryptography.hazmat.bindings.openssl.bio',
            'cryptography.hazmat.bindings.openssl.conf',
            'cryptography.hazmat.bindings.openssl.crypto',
            'cryptography.hazmat.bindings.openssl.dh',
            'cryptography.hazmat.bindings.openssl.dsa',
            'cryptography.hazmat.bindings.openssl.ec',
            'cryptography.hazmat.bindings.openssl.engine',
            'cryptography.hazmat.bindings.openssl.err',
            'cryptography.hazmat.bindings.openssl.evp',
            'cryptography.hazmat.bindings.openssl.hmac',
            'cryptography.hazmat.bindings.openssl.nid',
            'cryptography.hazmat.bindings.openssl.objects',
            'cryptography.hazmat.bindings.openssl.opensslv',
            'cryptography.hazmat.bindings.openssl.osrandom_engine',
            'cryptography.hazmat.bindings.openssl.pem',
            'cryptography.hazmat.bindings.openssl.pkcs7',
            'cryptography.hazmat.bindings.openssl.pkcs12',
            'cryptography.hazmat.bindings.openssl.rand',
            'cryptography.hazmat.bindings.openssl.rsa',
            'cryptography.hazmat.bindings.openssl.ssl',
            'cryptography.hazmat.bindings.openssl.x509',
            'cryptography.hazmat.bindings.openssl.x509name',
            'cryptography.hazmat.bindings.openssl.x509v3',
            'cryptography'
            ]

packages = ['cryptography']

includefiles += ['build_resources/NagiosSoftwareLicense.txt',
                 'build_resources/listener_init',
                 'build_resources/passive_init']

buildOptions = dict(includes=includes,
                    include_files=includefiles,
                    packages=packages)

base = None

setup(name = "NCPA",
      version = "1.4",
      description = "NCPA",
      options = dict(build_exe=buildOptions),
      executables = [Executable("ncpa_posix_listener.py", base=base), 
                     Executable("ncpa_posix_passive.py", base=base)])

