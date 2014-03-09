import sys
import os

tag = sys.argv[1]

os.system('python3.3 update.py "%s"' % tag)
os.system('python3.3 build.py')
os.system('python3.3 package.py')
