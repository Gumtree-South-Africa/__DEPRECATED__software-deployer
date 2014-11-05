#! /usr/bin/python

import os
import sys
import json
import argparse

from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.generators.servicecontrol import ServiceControl
from deployerlib.executor import Executor


parser = argparse.ArgumentParser()
action_group = parser.add_mutually_exclusive_group(required=True)
action_group.add_argument('--restartservice', nargs='+', metavar='SERVICE', help='Single service to restart')
action_group.add_argument('--disableservice', nargs='+', metavar='SERVICE', help='Single service to disable')
action_group.add_argument('--enableservice', nargs='+', metavar='SERVICE', help='Single service to enable')

log = Log(os.path.basename(__file__))

args = CommandLine(parents=parser)
config = Config(args)
servicecontrol = ServiceControl(config)
tasklist = servicecontrol.generate()
executor = Executor(tasklist=tasklist)

if config.dry_run:
    log.info('Dry run, not executing any tasks')
    print json.dumps(tasklist, indent=4, sort_keys=True)
    sys.exit(1)

executor.run()
