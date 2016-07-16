""" nd init command

Prints shell commands for auto-complete.

"""

from __future__ import print_function

import sys

import argparse
import pkg_resources


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(description='Sets up the bash autocomplete for nd-toolbelt.')
    parser.add_argument('app_args', choices=['-'],
                        help='The required syntax for this call is "nd init -".')
    parser.parse_args(argv[1:])

    print(pkg_resources.resource_string(__name__, '../nd-init.sh').decode('utf-8'))

if __name__ == "__main__":
    main(sys.argv)
