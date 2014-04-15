import fileinput
import os
import sys

BASEDIR = os.path.dirname(os.path.abspath(__file__))

version_file = open(os.path.join(BASEDIR, 'VERSION.md'), 'r')
VERSION = version_file.readline().strip()
version_file.close()

server_source = os.path.join(BASEDIR, 'agent', 'listener', 'server.py')

print server_source
# Now edit the listener/server.py to have that version
for line in fileinput.input(server_source, inplace=True):
    if line.startswith('__VERSION__'):
        print '__VERSION__ = %s' % VERSION,
    else:
        print line,
