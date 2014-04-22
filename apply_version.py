import fileinput
import os
import sys

BASEDIR = os.path.dirname(os.path.abspath(__file__))

version_file = open(os.path.join(BASEDIR, 'VERSION.md'), 'r')
VERSION = version_file.readline().strip()
version_file.close()

server_source = os.path.join(BASEDIR, 'agent', 'listener', 'server.py')
docs_config = os.path.join(BASEDIR, 'docs', 'conf.py')

# Now edit the listener/server.py to have that version
for line in fileinput.input(server_source, inplace=True):
    if line.startswith('__VERSION__'):
        print '__VERSION__ = %s' % VERSION
    else:
        print line,

for line in fileinput.input(docs_config, inplace=True):
    if line.startswith('version ='):
        print 'version = %s' % VERSION
    elif line.startswith('release ='):
        print 'release = %s' % VERSION
    else:
        print line,
