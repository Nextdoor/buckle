""" nd version command

Prints tool version.

"""


import nd_toolbelt.version


def main(*argv):
    print(nd_toolbelt.version.VERSION)

if __name__ == "__main__":
    main()
