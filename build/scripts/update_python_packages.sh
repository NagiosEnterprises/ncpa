#!/bin/bash -e

BASEDIR="$(dirname "$BASH_SOURCE")"
PYTHONVER=python3.5
PYTHONBIN=`which python3.5`

# Get OS info
. $BASEDIR/init.sh

if [ $dist == "el5" ]; then
    reqlist="require.el5"
else
    reqlist="require"
fi

# Update with requirements
$PYTHONBIN -m pip install -r $BASEDIR/../resources/$reqlist.txt --upgrade

echo "Python pip requirements updated."