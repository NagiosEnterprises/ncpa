#!/bin/bash -e

PYTHONBIN="python"

update_py_packages() {
    $PYTHONBIN -m pip install -r $BUILD_DIR/resources/require.txt --upgrade
}
