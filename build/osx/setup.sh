#!/bin/bash -e

PYTHONTAR="Python-2.7.14"
PYTHONBIN="python"
SKIP_PYTHON=0
CXFREEZEVER="cx_Freeze-4.3.4"
update_py_packages() {
    $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade
}

install_prereqs() {

    cd $BUILD_DIR/resources

    # Install bundled Python version from source
    if [ $SKIP_PYTHON -eq 0 ]; then
        tar xf $PYTHONTAR.tgz
        cd $PYTHONTAR
        ./configure LDFLAGS='-Wl,-rpath,\$${ORIGIN} -Wl,-rpath,\$${ORIGIN}/lib' && make && make altinstall
        cd ..
        rm -rf $PYTHONTAR
        PYTHONBIN=$(which python2.7)
    fi

    # Install the patched version of cx_Freeze
    tar xf $CXFREEZEVER.tar.gz
    cd $CXFREEZEVER
    $PYTHONBIN setup.py install
    cd ..
    rm -rf $CXFREEZEVER

    # --------------------------
    #  INSTALL PIP & PIP MODULES
    # --------------------------

    # Install pip
    cd /tmp && wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py && $PYTHONBIN /tmp/get-pip.py

    # Install modules
    update_py_packages

	# Add users/groups
	set +e
	sudo sysadminctl -addUser nagios
	sudo dseditgroup -o create nagios
	sudo dseditgroup -o edit -a nagios -t user nagios
	set -e
}

