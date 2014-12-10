#! /usr/bin/python

import os
import json
import argparse

from deployerlib.exceptions import DeployerException

from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.tasklist import Tasklist


json_opts = {'indent': 4, 'sort_keys': True}
log = Log(os.path.basename(__file__))

parser = argparse.ArgumentParser()
parser.add_argument('--dump', action='store_true', help='Dump the resulting task list')
parser.add_argument('--save', help='Save the resulting task list to a file')
component_group = parser.add_mutually_exclusive_group(required=True)
component_group.add_argument('--component', nargs='+', help='Specify a list of components to deploy')
component_group.add_argument('--release', '--directory', nargs='+', help='Specify a directory of components to deploy')

args = CommandLine(parents=parser)
config = Config(args)

try:
    tasklist_builder = Tasklist(config, config.platform)
except DeployerException as e:
    log.critical('Failed to generate task list: {0}'.format(e))
    sys.exit(1)

if config.dump:
    print json.dumps(tasklist_builder.tasklist, **json_opts)

if tasklist_builder.verify_tasklist() and config.save:
    with open(config.save, 'w') as f:
        json.dump(tasklist_builder.tasklist, f, **json_opts)
        log.info('Saved task list to {0}'.format(config.save))
