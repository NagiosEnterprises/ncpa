#!/bin/bash

set -e

if ! which gcc > /dev/null;
then
    echo 'gcc must be installed to continue.'
    exit 1
elif ! which wget > /dev/null;
then
    echo 'wget must be installed to continue.'
    exit 1
elif ! which make > /dev/null;
then
    echo 'make must be installed to continue.'
    exit 1
elif ! /sbin/ldconfig -p | grep ffi > /dev/null;
then
    echo 'must have libffi installed to continue.'
    exit 1
elif ! /sbin/ldconfig -p | grep ssl > /dev/null;
then
    echo 'must have openssl installed to continue.'
    exit 1
fi

# Build a Python for the system, regardless of whether or not it exists
PYTHONVER='3.3.4'
cd /tmp
wget "http://www.python.org/ftp/python/$PYTHONVER/Python-$PYTHONVER.tgz"
tar xf Python-$PYTHONVER.tgz
cd Python-$PYTHONVER
./configure --enable-shared --with-zlib=/usr/include
make
make altinstall
cd ..
rm -rf $PYTHONVER*
echo '/usr/local/lib' >> /etc/ld.so.conf
ldconfig

# Install pip
wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py --no-check-certificate
python3.3 get-pip.py
rm -f get-pip.py

# Install cx_Freeze
wget 'http://downloads.sourceforge.net/project/cx-freeze/4.3.2/cx_Freeze-4.3.2.tar.gz?r=http%3A%2F%2Fcx-freeze.sourceforge.net%2F&ts=1394344052&use_mirror=iweb' -O cx_Freeze-4.3.2.tar.gz
tar xf cx_Freeze-4.3.2.tar.gz
cd cx_Freeze-4.3.2
python3.3 setup.py install
cd ..
rm -rf cx_Freeze*

# Special install for werkzeug for now...
cd /tmp
git clone git://github.com/mitsuhiko/werkzeug.git
cd werkzeug
pip install --editable .
cd ..
rm werkzeug -rf
