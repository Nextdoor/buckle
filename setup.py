import sys
import codecs
from nd_toolbelt.version import VERSION

# Prevent spurious errors during `python setup.py test`, a la
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html:
try:
    import multiprocessing
except ImportError:
    pass

from setuptools import setup, find_packages


extra_setup = {}
if sys.version_info >= (3,):
    extra_setup['use_2to3'] = True

setup(
    name='nd-toolbelt',
    version=VERSION,
    description='Nextdoor Toolbelt',
    author='Dev Tools Team',
    author_email='dev-tools-team@nextdoor.com',
    packages=find_packages(exclude=['ez_setup']),
    scripts=['bin/nd', 'bin/nd-version'],
    install_requires=[
        'future>=0.15.2',
    ],
    tests_require=[
    ],
    url='https://https://git.corp.nextdoor.com/Nextdoor/nd-toolbelt',
    include_package_data=True,
    **extra_setup
)
