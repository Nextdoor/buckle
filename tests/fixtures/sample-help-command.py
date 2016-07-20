#!/usr/bin/env python
from __future__ import print_function

import argparse
import os
import sys

parser = argparse.ArgumentParser(
    description='Help for command {}'.format(os.path.basename(sys.argv[0])))
parser.parse_args()
