#! /usr/bin/python

import os
import json
import argparse

from deployerlib.exceptions import DeployerException
from deployerlib.generators import *

from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.executor import Executor

json_opts = {'indent': 4, 'sort_keys': True}

callables = {
    'pmcconnell': pmcconnell.DemoMatrix,
}

log = Log(os.path.basename(__file__))

parser = argparse.ArgumentParser()
parser.add_argument('--dump', action='store_true', help='Dump the resulting task list')
parser.add_argument('--save', help='Save the resulting task list to a file')
component_group = parser.add_mutually_exclusive_group(required=True)
component_group.add_argument('--component', nargs='+', help='Specify a list of components to deploy')
component_group.add_argument('--directory', help='Specify a directory of components to deploy')

args = CommandLine(parents=parser)
config = Config(args)

callable = callables.get(config.platform)

if not callable:
    raise DeployerException('No callable matrix defined for platform {0}'.format(config.platform))

platform_config = callable(config=config)
tasklist = platform_config.build_matrix()

if tasklist:
    log.info('Verifying syntax of task list')
    executor = Executor(tasklist=tasklist)
    del executor
else:
    log.warning('Task list is empty')

if config.dump:
    print json.dumps(tasklist, **json_opts)

if config.save:
    with open(config.save, 'w') as f:
        json.dump(tasklist, f, **json_opts)
        log.info('Saved task list to {0}'.format(config.save))
