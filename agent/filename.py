#!/usr/bin/env python

import sys
import os


def get_dirname_file():
    if getattr(sys, u'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(__file__)
