#! /usr/bin/python

import argparse

from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.executor import Executor

# Add command line option for components to deploy
parser = argparse.ArgumentParser()
parser.add_argument('--tasklist', help='A list of pre-generated tasks', required=True)

args = CommandLine(parents=parser, require_config=False)

executor = Executor(args.tasklist)
executor.run()
