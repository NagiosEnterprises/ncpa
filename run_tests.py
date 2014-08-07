import os
import nose
import sys

script_dirname = os.path.dirname(os.path.abspath(__file__))
agent_path = os.path.join(script_dirname, 'agent')
client_path = os.path.join(script_dirname, 'client')

sys.path.append(agent_path)

nose.run()

