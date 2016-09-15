import argparse
import textwrap


class DedentDescriptionArgumentDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """Help message formatter which provides defaults and dedents the help text.

    The methods we use are not part of a public API so this may need to be updated for different
    versions.
    """

    def _fill_text(self, text, width, indent):
        return textwrap.dedent(text)
