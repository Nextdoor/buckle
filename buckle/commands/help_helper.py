from __future__ import print_function

import argparse
import os
import sys

BUILTIN_TOOLBELT_NAME = 'buckle'

HELP_DESCRIPTION = """\
Bash helper for creating program descriptions that can be included by buckle help.

Insert $({toolbelt_name} _help-helper "<your help text>") at the top of a bash script to add a
description that shows up when running '{toolbelt_name} help'.

Example usage:

#!/usr/bin/env bash
eval "$({toolbelt_name} _help-helper" "Prints the time"
date
"""

OUTPUT = """\
# Print help message consisting arguments passed to the original program
if [[ "$1" = "--help" ]]; then
    echo "{message}"
    exit 0
fi\
"""


def main(argv=sys.argv):
    toolbelt_name = os.getenv('BUCKLE_TOOLBELT_NAME', BUILTIN_TOOLBELT_NAME)
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=HELP_DESCRIPTION.format(toolbelt_name=toolbelt_name))
    parser.add_argument('message', metavar='N', nargs='+', help='Help message')
    args = parser.parse_args(sys.argv[1:])

    print(OUTPUT.format(message=' '.join(args.message)))

if __name__ == "__main__":
    main(sys.argv)
