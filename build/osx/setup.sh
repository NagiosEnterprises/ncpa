#!/bin/bash -e

echo -e "***** osx/setup.sh"

PYTHONVER="3.9.13"
PYTHONTAR="Python-$PYTHONVER"
PYTHONBIN=$(which python3.9)
SKIP_PYTHON=0

update_py_packages() {
    $PYTHONBIN -m pip install --upgrade pip
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
        PYTHONBIN=$(which python3.9)
    fi

    # Install modules
    update_py_packages

	# Add users/groups
	set +e
	sudo sysadminctl -addUser nagios
	sudo dseditgroup -o create nagios
	sudo dseditgroup -o edit -a nagios -t user nagios
	set -e
}

