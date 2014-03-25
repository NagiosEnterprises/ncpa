import os
import sys

script_dir = os.path.abspath(os.path.dirname(__file__))

if sys.platform.startswith('win'):
    build_target = 'setup.py'
else:
    build_target = 'posix.py'

os.chdir(os.path.join(script_dir, '..', 'agent'))
os.system('find . -type d -name __pycache__ -exec rm -rf {} \;')

version_file = open('../VERSION.md', 'r')
__VERSION__ = '%.1f' % float(version_file.readlines()[0])

log = open('var/ncpa_listener.log', 'w')
log.close()

log = open('var/ncpa_passive.log', 'w')
log.close()

os.system('python3.3 %s build_exe' % build_target)

os.chdir('../docs')

os.system('make html')
os.system('mv _build/html ../agent/build/*/listener/static/help')

os.chdir('../agent')

if not sys.platform.startswith('win'):
    os.system('rm -rf /tmp/ncpa-%s' % __VERSION__)
    os.mkdir('/tmp/ncpa-%s' % __VERSION__)
    os.system('cp build/*/* /tmp/ncpa-%s -rf' % __VERSION__)
    os.chdir('/tmp')
    os.system('tar zcvf %s/ncpa-%s.tar.gz ncpa-%s' % (script_dir, __VERSION__, __VERSION__)) 
    print('%s/ncpa-%s.tar.gz' % (script_dir, __VERSION__))
