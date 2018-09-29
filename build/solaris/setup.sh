#!/bin/bash

# Update path to include csw on Solaris
PATH=$PATH:/opt/csw/bin:/usr/ccs/bin

# Globals
PYTHONTAR="Python-2.7.14"
PYTHONVER="python2.7"
PYTHONBIN="/usr/local/bin/python2.7"
CXFREEZEVER="cx_Freeze-4.3.4"

install_prereqs() {


    # --------------------------
    #  INSTALL SYSTEM REQS
    # --------------------------


    # Check version of Solaris
    SOLARIS=11
    if cat /etc/release | grep s10x > /dev/null ; then
        SOLARIS=10
    fi

    # Install pre-reqs for Solaris systems
    if [ $SOLARIS -eq 10 ]; then
        pkgutil -y -i python27 python27_dev
        PYTHONBIN="python2.7"
    else
        pkg install gcc libffi zlib
    fi


    # --------------------------
    #  INSTALL SOURCE FILES
    # --------------------------


    cd $BUILD_DIR/resources

    # Install bundled Python version from source if needed
    if [ $SOLARIS -eq 11 ]; then
        tar xf $PYTHONTAR.tgz
        cd $PYTHONTAR
        ./configure --with-zlib=/usr/include --enable-shared && make && make altinstall
        cd ..
        rm -rf $PYTHONTAR
    fi

    # Install the patched version of cx_Freeze
    gunzip $CXFREEZEVER.tar.gz
    tar xf $CXFREEZEVER.tar
    cd $CXFREEZEVER
    $PYTHONBIN setup.py install
    cd ..
    rm -rf $CXFREEZEVER


    # --------------------------
    #  INSTALL PIP & PIP MODULES
    # --------------------------


    # Install pip
    cd /tmp && wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py && $PYTHONBIN /tmp/get-pip.py

    # Install pip python modules
    CFLAGS="-I/usr/lib/amd64/libffi-3.2.1/include" $PYTHONBIN -m pip install -r $BASEDIR/../resources/require.txt --upgrade


    # --------------------------
    #  MISC ADDITIONS
    # --------------------------


    useradd nagios
    groupadd nagios
    usermod -g nagios nagios

}
