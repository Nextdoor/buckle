""" buckle init command

Prints shell commands for auto-complete.

"""

from __future__ import print_function

import os
import sys

import argparse
import pkg_resources


SETUP_SCRIPT = """\
_buckle_autocomplete_setup "{toolbelt_name}"
alias "{toolbelt_name}='BUCKLE_TOOLBELT_NAME={toolbelt_name} buckle'"
"""


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(description='Sets up the bash autocomplete for a toolbelt.')
    parser.add_argument('toolbelt_name',
                        help='The required syntax for this call is "buckle init <toolbelt name>".')
    args = parser.parse_args(argv[1:])
    if args.toolbelt_name == '-':
        args.toolbelt_name = os.getenv('BUCKLE_TOOLBELT_NAME', os.path.basename(argv[0]))

    print(pkg_resources.resource_string(__name__, '../init.sh').decode('utf-8'))
    print(SETUP_SCRIPT.format(toolbelt_name=args.toolbelt_name))

if __name__ == "__main__":
    main(sys.argv)
