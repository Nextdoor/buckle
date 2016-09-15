from buckle.version import VERSION

from setuptools import setup, find_packages

setup(
    name='buckle',
    version=VERSION,
    description='Buckle: It ties your toolbelt together',
    author='Nextdoor',
    author_email='eng@nextdoor.com',
    packages=find_packages(exclude=['ez_setup']),
    scripts=['bin/buckle',
             'bin/buckle-init',
             'bin/buckle-help',
             'bin/buckle-_help-helper',
             'bin/buckle-readme',
             'bin/buckle-version',
             ],
    test_suite="tests",
    install_requires=[
        'future>=0.15.2',
    ],
    tests_require=[
        'pytest',
    ],
    url='https://git.corp.nextdoor.com/Nextdoor/buckle',
    include_package_data=True
)
