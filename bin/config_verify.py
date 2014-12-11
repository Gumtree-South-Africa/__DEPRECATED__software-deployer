#! /usr/bin/python

import sys
import argparse
import yaml
from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.exceptions import DeployerException


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
log = Log(os.path.basename(__file__))
args.verify_config = True
config = Config(args)
log.info('Config Verify completed. More details in {0}'.format(log.get_logfile()))
