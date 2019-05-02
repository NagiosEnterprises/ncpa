#!/bin/bash

# Update path to include csw on Solaris
PATH=$PATH:/opt/csw/bin:/usr/ccs/bin

# Globals
PYTHONTAR="Python-2.7.14"
PYTHONVER="python2.7"
PYTHONBIN=$(which python2.7)
CXFREEZEVER="cx_Freeze-4.3.4"

# Check version of Solaris
SOLARIS=11
ARCH="x86"
LIBFFI_DEV="/usr/lib/amd64/libffi-3.2.1/include"
if grep "SPARC" /etc/release > /dev/null ; then
    ARCH="sparc"
fi
if grep "Solaris 10" /etc/release > /dev/null ; then
    SOLARIS=10
    PYTHONBIN="/opt/csw/bin/python2.7"
    LIBFFI_DEV="/opt/csw/lib/amd64/libffi-3.2.1/include"
    if [ "$ARCH" == "sparc" ]; then
        LIBFFI_DEV="/opt/csw/lib/libffi-3.2.1/include"
    fi
fi

update_py_packages() {
    if [ "$ARCH" == "sparc" ] && [ $SOLARIS -eq 11 ]; then
        $PYTHONBIN -m pip install -r  $BUILD_DIR/solaris/require.sparc.txt --upgrade
    else
        CPPFLAGS="-I$LIBFFI_DEV" $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade --no-binary=greenlet
    fi
}

install_prereqs() {


    # --------------------------
    #  INSTALL SYSTEM REQS
    # --------------------------


    # Install pre-reqs for Solaris systems
    if [ $SOLARIS -eq 10 ]; then
        pkgutil -y -i gcc5core python27 python27_dev py_pip wget libffi_dev libssl_dev        
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
        ./configure && make && make altinstall
        cd ..
        rm -rf $PYTHONTAR
    fi

    # Install the patched version of cx_Freeze
    if [ $SOLARIS -eq 11 ]; then
        tar xf $CXFREEZEVER.tar.gz
    else
        gunzip $CXFREEZEVER.tar.gz
        tar xf $CXFREEZEVER.tar
    fi
    cd $CXFREEZEVER
    $PYTHONBIN setup.py install
    cd ..
    rm -rf *.h
    rm -rf $CXFREEZEVER


    # --------------------------
    #  INSTALL PIP & PIP MODULES
    # --------------------------


    # Install pip
    cd /tmp && wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py && $PYTHONBIN /tmp/get-pip.py

    # Install pip python modules
    update_py_packages


    # --------------------------
    #  MISC ADDITIONS
    # --------------------------


    useradd nagios
    groupadd nagios
    usermod -g nagios nagios


}
