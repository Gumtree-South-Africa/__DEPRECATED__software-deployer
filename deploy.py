#! /usr/bin/python

import os
import argparse

from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.executor import Executor
from deployerlib.exceptions import DeployerException

parser = argparse.ArgumentParser()
parser.add_argument('--tasklist', help='A list of pre-generated tasks', required=True)

log = Log(os.path.basename(__file__))
args = CommandLine(parents=parser, require_config=False)
executor = Executor(args.tasklist)

try:
    executor.run()
except DeployerException as e:
    log.critical('Execution failed: {0}'.format(e))
