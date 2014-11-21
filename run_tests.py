"""Python test runner. Use this because the necessary paths can be
tough to get right::

    python run_tests.py [agent] [client]
"""

import os
import nose
import sys


def main():
    """Add the proper paths to the path.

    """
    script_dirname = os.path.dirname(os.path.abspath(__file__))
    agent_path = os.path.join(script_dirname, 'agent')
    client_path = os.path.join(script_dirname, 'client')

    sys.path.append(agent_path)
    sys.path.append(client_path)

if __name__ == "__main__":
    main()
    nose.run()
