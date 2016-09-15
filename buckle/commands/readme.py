""" nd readme command

Prints the README.md file, interactively if possible.

"""

from __future__ import print_function

import argparse
import os
import pkg_resources
import subprocess
import sys

README_PATH = '../README.md'


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='View the README.md for buckle project.')
    parser.add_argument('--interactive', action='store_true', default=None,
                        help='Use interactive markdown viewer')
    args = parser.parse_args(argv[1:])

    if args.interactive is None:
        try:
            subprocess.check_output(['tty', '-s'])
        except subprocess.CalledProcessError:
            use_markdown_viewer = False
        else:
            use_markdown_viewer = True
    else:
        use_markdown_viewer = args.interactive

    if use_markdown_viewer:
        readme_filename = pkg_resources.resource_filename(__name__, README_PATH)
        readme_sh = pkg_resources.resource_filename(__name__, 'readme.sh')
        os.execv(readme_sh, [readme_sh, readme_filename])
    else:
        # Non-interactive mode
        readme = pkg_resources.resource_stream(__name__, README_PATH)
        for line in readme:
            print(line.decode('utf-8'), end='')

if __name__ == "__main__":
    main(sys.argv)
