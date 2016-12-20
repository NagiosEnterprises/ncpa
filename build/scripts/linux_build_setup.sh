#!/bin/bash
#
# Linux Build Server Setup Script
# Creates a functioning build environment on a linux server
#

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHONTAR="Python-2.7.13"
PYTHONVER="python2.7"
CXFREEZETAR="cx_Freeze-4.3.4-patched"
CXFREEZEVER="cx_Freeze-4.3.4"
GWEBSOCKETTAR="gevent-websocket-0.9.5-patched"
GWEBSOCKETVER="gevent-websocket-0.9.5"
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

# Install the patched version of cx_Freeze
cd ..
tar xf $CXFREEZETAR.tar.gz
cd $CXFREEZEVER
$PYTHONBIN setup.py install

# Install cx_Logging
cd ..
tar xf $CXLOGGINGVER.tar.gz
cd $CXLOGGINGVER
$PYTHONBIN setup.py install

# Install cx_PyGenLib
cd ..
tar xf $CXPYGENLIBVER.tar.gz
cd $CXPYGENLIBVER
$PYTHONBIN setup.py install

# Clean up resource directory
cd ..
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

cd $DIR
$PYTHONBIN -m pip install -r ../resources/require.txt --upgrade

# --------------------------
#  INSTALL RESOURCES
# --------------------------

# Install patched version of gevent-websocket
cd $DIR/../resources

tar xf $GWEBSOCKETTAR.tar.gz
cd $GWEBSOCKETVER
$PYTHONBIN setup.py install

# Clean up resources directory again
cd ..
rm -rf $GWEBSOCKETVER

# --------------------------
#  MISC SETUP
# --------------------------

# Add users if they don't exist
useradd nagios
groupadd nagios
