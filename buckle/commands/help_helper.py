from __future__ import print_function

import argparse
import os
import sys


HELP_DESCRIPTION = """\
Bash helper for creating program descriptions that can be included by buckle help.

Insert $({toolbelt_name} _help-helper "<your help text>") at the top of a bash script to add a description that
shows up when running '{toolbelt_name} help'.

Example usage:

#!/usr/bin/env bash
eval "$({toolbelt_name} _help-helper "Prints the time")"
date
"""

OUTPUT = """\
# Print help message consisting arguments passed to the original program
if [[ "\$1" = "--help" ]]; then
    echo "${@}"
    exit 0
fi\
"""


def main(argv=sys.argv):
    toolbelt_name = os.path.basename(argv[0])
    parser = argparse.ArgumentParser(
        description=HELP_DESCRIPTION.format(toolbelt_name=toolbelt_name))

    parser.parse_args(sys.argv[1:])

    print(OUTPUT)

if __name__ == "__main__":
    main(sys.argv)
