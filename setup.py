import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="software-deployer",
    version="1.0.59",
    author="Patrick McConnell",
    author_email="pmcconnell@ebay.com",
    description=("A modular, extendable, configuration-driven deployment system."),
    license="GPL",
    keywords="python software deployment",
    url="https://github.scm.corp.ebay.com/ecg-marktplaats/software-deployer",
    packages=['deployerlib', 'deployerlib.commands', 'deployerlib.generators', 'deployerweb', 'deployerweb.migrations'],
    include_package_data=True,
    zip_safe=False,
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: GPL License",
    ],
    install_requires=[
        "nsnitro",
        "attrdict<=1.0.1",
        'Fabric',
        'requests',
    ],
    scripts=[
        'bin/deploy.py',
        'bin/build_tasklist.py',
        'bin/servicecontrol.py',
        'bin/deploywebapp.py',
        'bin/deploywebmanage.py',
        "bin/createpackage.py",
        "bin/jenkins_upstreams_project_hashes.py"
    ],
)
