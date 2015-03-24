#! /usr/bin/env python2.7

import os
import sys
import json
import argparse

from deployerlib.exceptions import DeployerException

from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.tasklist import Tasklist


json_opts = {'indent': 4, 'sort_keys': True}

parser = argparse.ArgumentParser()
parser.add_argument('--dump', action='store_true', help='Dump the resulting task list')
parser.add_argument('--save', help='Save the resulting task list to a file')
component_group = parser.add_mutually_exclusive_group(required=True)
component_group.add_argument('--component', nargs='+', help='Specify a list of components to deploy')
component_group.add_argument('--release', '--directory', nargs='+', help='Specify a directory of components to deploy')

try:
    args = CommandLine(parents=parser)
    log = Log(os.path.basename(__file__))
    config = Config(args)
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

log.info('Build tasklist completed. More details in {0}'.format(log.get_logfile()))
