from nd_toolbelt.version import VERSION

from setuptools import setup, find_packages

setup(
    name='nd-toolbelt',
    version=VERSION,
    description='Nextdoor Toolbelt',
    author='Dev Tools Team',
    author_email='dev-tools-team@nextdoor.com',
    packages=find_packages(exclude=['ez_setup']),
    scripts=['bin/nd',
             'bin/nd-init',
             'bin/nd-help',
             'bin/nd-readme',
             'bin/nd-version',
             ],
    test_suite="tests",
    install_requires=[
        'future>=0.15.2',
    ],
    tests_require=[
        'pytest',
    ],
    url='https://https://git.corp.nextdoor.com/Nextdoor/nd-toolbelt',
    include_package_data=True
)
