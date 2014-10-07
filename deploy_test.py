#! /usr/bin/python

import os
import sys
import argparse

from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.orchestrator import Orchestrator

# Add command line option for components to deploy
parser = argparse.ArgumentParser()
component_group = parser.add_mutually_exclusive_group(required=True)
component_group.add_argument('--component', nargs='+', help='Specify a list of components to deploy')
component_group.add_argument('--directory', help='Specify a directory of components to deploy')

args = CommandLine(parents=parser)
c = Config(args)
config = c.get()

orchestrator = Orchestrator(config)
orchestrator.run()
