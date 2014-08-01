import os
import shutil
import subprocess
import sys

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
nsi_store = os.path.join(basedir, 'agent', 'build_resources', 'ncpa.nsi')
nsi = os.path.join(basedir, 'agent', 'build', 'ncpa.nsi')
nsis = os.environ['PROGRAMFILES'] + '/NSIS/makensis'

os.chdir(basedir)

with open('VERSION.md') as version_file:
    version = version_file.readline().strip()

try:
	os.remove(os.path.join(basedir, 'build', 'ncpa-%s.exe' % version))
except:
	pass

subprocess.Popen(['git', 'pull']).wait()
subprocess.Popen(['pip', 'install', '-r', os.path.join(basedir, 'requirements.txt')]).wait()
subprocess.Popen(['rmdir', os.path.join(basedir, 'agent', 'build'), '/s', '/q'], shell=True).wait()

os.chdir('docs')
subprocess.Popen(['make.bat', 'html']).wait()

os.chdir('../agent')

if not os.path.exists('var'):
    os.mkdir('var')
open(os.path.join('var', 'ncpa_listener.log'), 'w')
open(os.path.join('var', 'ncpa_passive.log'), 'w')

if not os.path.exists('plugins'):
    os.mkdir('plugins')
	
sys.path.append(os.getcwd())
subprocess.Popen(['python', 'setup_windows.py', 'build_exe']).wait()

#os.remove(os.path.join(basedir, 'agent', 'build', 'NCPA', 'listener', 'static', 'help'))
shutil.copytree(os.path.join(basedir, 'docs', '_build', 'html'), 
                os.path.join(basedir, 'agent', 'build', 'NCPA', 'listener', 'static', 'help'))

shutil.copy(nsi_store, nsi)
b = subprocess.Popen([nsis, nsi])
b.wait()

print os.path.join(basedir, 'agent', 'build', 'NCPA_Installer.exe')
print os.path.join(basedir, 'build', 'ncpa-%s.exe' % version)

shutil.copyfile(os.path.join(basedir, 'agent', 'build', 'NCPA_Installer.exe'),
                os.path.join(basedir, 'build', 'ncpa-%s.exe' % version))
