import os
import sys

script_dir = os.path.dirname(__file__)

if sys.platform == 'nt':
    build_target = 'setup.py'
else:
    build_target = 'posix.py'

os.chdir(os.path.join(script_dir, '..', 'agent'))

log = open('var/ncpa_listener.log', 'w')
log.close()

log = open('var/ncpa_passive.log', 'w')
log.close()

os.system('python3.3 %s build_exe' % build_target)
