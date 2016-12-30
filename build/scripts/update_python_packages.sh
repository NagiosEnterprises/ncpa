#!/bin/bash -e

PYTHONVER=python2.7
PYTHONBIN=`which python2.7`

# Get OS info
./init.sh

if [ $ver == "el5" ]; then
	reqlist="require.el5"
else
	reqlist="require"
fi

# Update with requirements
$PYTHONBIN -m pip install -r ../resources/$reqlist.txt --upgrade

echo "Python pip requirements updated."