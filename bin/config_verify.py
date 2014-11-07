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

args = CommandLine(parents=parser)
config = Config(args)
config_structure = config._get_config_struct()
config.vrfy_w_recurse(config,config_structure)
#config.verify()
