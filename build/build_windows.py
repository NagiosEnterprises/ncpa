import os
import shutil
import subprocess
import sys

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
nsi = os.path.join(basedir, 'agent', 'build', 'ncpa.nsi')
nsis = 'C:/Program Files/NSIS/makensis'

os.chdir(basedir)

os.chdir('docs')
os.system('make.bat html')
os.chdir('../agent')

if not os.path.exists('var'):
    os.mkdir('var')
open(os.path.join('var', 'ncpa_listener.log'), 'w')
open(os.path.join('var', 'ncpa_passive.log'), 'w')

if not os.path.exists('plugins'):
    os.mkdir('plugins')
	
sys.path.append(os.getcwd())
os.system('python2.7 setup_windows.py build_exe')

shutil.rmtree('build/exe.win32-2.7/listener/static/help', ignore_errors=True)
shutil.copytree('../docs/_build/html', 'build/exe.win32-2.7/listener/static/help')

b = subprocess.Popen([nsis, nsi])
b.wait()
