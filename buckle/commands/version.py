""" nd version command

Prints tool version.

"""


import buckle.version


def main(*argv):
    print(buckle.version.VERSION)

if __name__ == "__main__":
    main()
