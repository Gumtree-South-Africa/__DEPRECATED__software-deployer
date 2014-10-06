#! /usr/bin/python

import os
import sys

from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.orchestrator import Orchestrator


args = CommandLine(require_component=True)
c = Config(args)
config = c.get()

orchestrator = Orchestrator(config)
orchestrator.run()
