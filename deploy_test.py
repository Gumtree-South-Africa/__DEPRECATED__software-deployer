#! /usr/bin/python

import os
import sys

from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.deployer import Deployer


args = CommandLine(require_component=True)
c = Config(args)
config = c.get()
deployer = Deployer(config)

deployer.deploy()
