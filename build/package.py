import shutil
import sys
import os

def make_rpm():
    v = open('../VERSION.md')
    version = v.readlines()[0].strip()
    os.system('rpmdev-setuptree')
    os.system('cp ncpa-%s.tar.gz ~/rpmbuild/SOURCES/' % version)
    os.system('cp ncpa.spec ~/rpmbuild/SPECS/ -f')

def make_deb():
    pass

def make_nsi():
    pass

def make_app():
    pass

if shutil.which('rpm'):
    make_rpm()
elif shutil.which('dpkg'):
    make_deb()
elif sys.platfrom.startswith('win'):
    make_nsi()
elif sys.platform == 'darwin':
    make_app()
else:
    print('I do no know what kind of system this is.')
