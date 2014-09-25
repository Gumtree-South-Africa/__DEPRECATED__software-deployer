#! /usr/bin/python

import os
import sys

from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.deployer import Deployer


args = CommandLine()
config = Config(args.config)
deployer = Deployer(args, config)

deployer.pre_deploy()
deployer.deploy()
