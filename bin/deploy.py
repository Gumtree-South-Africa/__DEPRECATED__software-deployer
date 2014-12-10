#! /usr/bin/python

import os
import sys
import argparse

from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.tasklist import Tasklist
from deployerlib.executor import Executor
from deployerlib.exceptions import DeployerException

parser = argparse.ArgumentParser()
component_group = parser.add_mutually_exclusive_group(required=True)
component_group.add_argument('--component', nargs='+', help='Specify a list of components to deploy')
component_group.add_argument('--release', '--directory', nargs='+', help='Specify a directory of components to deploy')
component_group.add_argument('--tasklist', help='A list of pre-generated tasks')

log = Log(os.path.basename(__file__))
args = CommandLine(parents=parser, require_config=False)

if args.tasklist:
    log.debug('Executing based on tasklist: {0}'.format(args.tasklist))
    executor = Executor(filename=args.tasklist)
elif args.config:
    log.debug('Executing based on config file: {0}'.format(args.config))
    config = Config(args)

    try:
        tasklist_builder = Tasklist(config, config.platform)
    except DeployerException as e:
        log.critical('Failed to generate task list: {0}'.format(e))
        sys.exit(1)

    if not tasklist_builder.tasklist:
        log.warning('Nothing to deploy')
        sys.exit(1)

    executor = Executor(tasklist=tasklist_builder.tasklist)

    if config.dry_run:
        log.info('Dry run, not executing any tasks')
        sys.exit(0)

else:
    log.critical('Do what?')
    sys.exit(1)

try:
    executor.run()
except DeployerException as e:
    log.critical('Execution failed: {0}'.format(e))
    sys.exit(1)
