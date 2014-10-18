#! /usr/bin/python

import argparse

from deployerlib.commandline import CommandLine
from deployerlib.executor import Executor

# Add command line option for components to deploy
parser = argparse.ArgumentParser()
component_group = parser.add_mutually_exclusive_group(required=False)
component_group.add_argument('--component', nargs='+', help='Specify a list of components to deploy')
component_group.add_argument('--directory', help='Specify a directory of components to deploy')
parser.add_argument('--tasklist', help='A list of pre-generated tasks')

args = CommandLine(parents=parser, require_config=False)

executor = Executor(args.tasklist)
executor.run()
