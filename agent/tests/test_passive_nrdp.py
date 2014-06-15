import os
import sys
import unittest

basepath = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')

sys.path.append(basepath)
from passive.abstract import *


class TestNRDPHandler(unittest.TestCase):

    def setUp(self):
        self.handler = nrdp.Handler()


if __name__ == '__main__':
    unittest.main()
