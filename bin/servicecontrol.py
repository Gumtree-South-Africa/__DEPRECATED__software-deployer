#! /usr/bin/env python2.7

import os
import sys
import json
import argparse

from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.generators.servicecontrol import ServiceControl
from deployerlib.executor import Executor
from deployerlib.exceptions import DeployerException

parser = argparse.ArgumentParser()
action_group = parser.add_mutually_exclusive_group(required=True)
action_group.add_argument('--restartservice', nargs='+', metavar='SERVICE', help='Single service to restart')
action_group.add_argument('--disableservice', nargs='+', metavar='SERVICE', help='Single service to disable (WARNING: No LB control)')
action_group.add_argument('--enableservice', nargs='+', metavar='SERVICE', help='Single service to enable (WARNING: No LB control)')
action_group.add_argument('--listservices', action='store_true', help='Lists services on a host')

args = CommandLine(parents=parser)
log = Log(os.path.basename(__file__))
config = Config(args)

try:
    generator = ServiceControl(config)
    tasklist = generator.generate()
    if config.dry_run:
        log.info('Dry run, not executing any tasks')
        print json.dumps(tasklist, indent=4, sort_keys=True)
        sys.exit(0)
    executor = Executor(tasklist=tasklist)
    executor.run()
except DeployerException as e:
    log.critical('Execution failed: {0}'.format(e))

log.info('ServiceControl completed. More details in {0}'.format(log.get_logfile()))
