import os
import nose
import sys

script_abs_path = os.path.abspath(__file__)

agent_dir = os.path.dirname(script_abs_path)
sys.path.append(agent_dir)
os.chdir(agent_dir)

nose.run()

