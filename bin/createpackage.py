#! /usr/bin/env python2.7

import argparse
import os
import sys

from deployerlib.log import Log
from deployerlib.config import Config
from deployerlib.commandline import CommandLine
from deployerlib.executor import Executor
from deployerlib.exceptions import DeployerException

from deployerlib.generators.auroraint import AuroraIntGenerator

parser = argparse.ArgumentParser()
parser.add_argument('--packagegroup', help='create deploy package for a group of services')
parser.add_argument('--destination', help='directory to move packages to')

log = Log(os.path.basename(__file__))
args = CommandLine(parents=parser)
config = Config(args)

aurora_int = AuroraIntGenerator(config)
tasklist = aurora_int.generate()
if not tasklist:
    log.critical("No tasks defined, aborting")
    sys.exit(1)

executor = Executor(tasklist=tasklist)
try:
    executor.run()
except DeployerException as e:
    more_details_msg = 'More details in {0}'.format(log.get_logfile())
    log.critical('Execution failed: {0}. {1}'.format(e, more_details_msg))
    sys.exit(1)
