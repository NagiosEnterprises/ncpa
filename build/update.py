#!/usr/bin/env python

import os
import sys

git_tag = sys.argv[1]
script_dir = os.path.dirname(__file__)

os.chdir(os.path.join(script_dir, '..'))

os.system('git pull')
os.system('git checkout %s' % git_tag)
os.system('pip3.3 install -r requirements.txt --upgrade')


