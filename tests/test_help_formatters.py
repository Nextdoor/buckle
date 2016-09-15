import argparse

from buckle import help_formatters


def test_dedent_argument_defaults_help_formatter():
    args = argparse.ArgumentParser(
        formatter_class=help_formatters.DedentDescriptionArgumentDefaultsHelpFormatter,
        description="""\
    First line
    Second line\
    """)
    assert '\nFirst line\nSecond line' in args.format_help()
