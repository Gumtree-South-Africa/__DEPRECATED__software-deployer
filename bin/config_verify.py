#! /usr/bin/python

import sys
import argparse
import yaml
from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.exceptions import DeployerException

log = Log('config_verify')

# Add command line option for components to deploy
parser = argparse.ArgumentParser()
#parser.add_argument('--servicename', help='Specify the service name to act on', required=True)
parser.add_argument('--dump', action='store_true', help='Dump the resulting task list')
parser.add_argument('--save', help='Save the resulting task list to a file')
component_group = parser.add_mutually_exclusive_group(required=False)
component_group.add_argument('--component', nargs='+', help='Specify a list of components to deploy')
component_group.add_argument('--release', '--directory', nargs='+', help='Specify a directory of components to deploy')
component_group.add_argument('--tasklist', help='A list of pre-generated tasks')


args = CommandLine(parents=parser)
args.verify_config = True
config = Config(args)
#if config.config_ok():
#    log.info('All tests passed, config ok')
#else:
#    log.error('Config verify found errors')
