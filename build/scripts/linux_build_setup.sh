#!/bin/bash
#
# Linux Build Server Setup Script
# Creates a functioning build environment on a linux server
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHONTAR="Python-2.7.11"
PYTHONVER="python2.7"
CXFREEZETAR="cx_Freeze-4.3.4-patched"
CXFREEZEVER="cx_Freeze-4.3.4"
CXLOGGINGVER="cx_Logging-2.1"
CXPYGENLIBVER="cx_PyGenLib-3.0"
PYTHONBIN="/usr/local/bin/python2.7"

# --------------------------
#  INSTALL PRE-REQS
# --------------------------
./linux_build_prereqs.sh

# --------------------------
#  INSTALL RESOURCES
# --------------------------

cd $DIR/../resources

# Install Python
tar xf $PYTHONTAR.tgz
cd $PYTHONTAR && ./configure --with-zlib=/usr/include --enable-shared && make && make altinstall
echo '/usr/local/lib' >> /etc/ld.so.conf 
/sbin/ldconfig

# Install cx_Freeze patched version
cd ..
tar xf $CXFREEZETAR.tar.gz
cd $CXFREEZEVER && $PYTHONBIN setup.py

# Install cx_Logging
cd ..
tar xf $CXLOGGINGVER.tar.gz
cd $CXLOGGINGVER && $PYTHONBIN setup.py

# Install cx_PyGenLib
cd ..
tar xf $CXPYGENLIBVER.tar.gz
cd $CXPYGENLIBVER && $PYTHONBIN setup.py

# Clean up resource directory
rm -rf $PYTHONTAR
rm -rf $CXFREEZEVER
rm -rf $CXLOGGINGVER
rm -rf $CXPYGENLIBVER

# --------------------------
#  INSTALL PIP
# --------------------------

cd /tmp && wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py && $PYTHONBIN /tmp/get-pip.py

# --------------------------
#  INSTALL PIP COMPONENTS
# --------------------------

$PYTHONBIN -m pip install gevent gevent-websocket flask jinja2 requests pyOpenSSL sphinx docutils sphinx-bootstrap-theme psutil

# --------------------------
#  MISC SETUP
# --------------------------

# Add users if they don't exist
useradd nagios
groupadd nagios
