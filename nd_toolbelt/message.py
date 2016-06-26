from __future__ import print_function

import os
import sys

GREEN = '\033[32m'
YELLOW = '\033[33m'
RED = '\033[31m'
EXIT = '\033[0m'

INFO = 'info'
WARNING = 'warning'
ERROR = 'error'

LEVEL_COLOR_MAP = {
    INFO: GREEN,
    WARNING: YELLOW,
    ERROR: RED
}


def write(msg, level, prefix='nd:'):
    """Prints a message to stderr with a color assigned based on its level. Informational messages
    are green, warnings are yellow, and errors are red. The given prefix is prepended to the message
    for namespace identification. If $TERM is not set, no color escape sequences are added.

    Args:
        msg: Given message
        level: stderr 'level' priority. Must be INFO, WARNING, or ERROR.
        prefix: Given namespace of the project calling this library.
    """
    msg = level.upper() + ': ' + prefix + ' ' + msg

    if os.getenv('TERM'):
        msg = LEVEL_COLOR_MAP[level] + msg + EXIT

    print(msg, file=sys.stderr)


def info(msg, **kwargs):
    write(msg, INFO, **kwargs)


def warning(msg, **kwargs):
    write(msg, WARNING, **kwargs)


def error(msg, **kwargs):
    write(msg, ERROR, **kwargs)
