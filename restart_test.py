#! /usr/bin/python

import argparse

from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.service import Service
from deployerlib.restarter import Restarter

parser = argparse.ArgumentParser()
action_group = parser.add_mutually_exclusive_group(required=True)
action_group.add_argument('--restartservice', metavar='SERVICE', help='Single service to restart')
action_group.add_argument('--disableservice', metavar='SERVICE', help='Single service to disable')
action_group.add_argument('--enableservice', metavar='SERVICE', help='Single service to enable')
action_group.add_argument('--listservices', metavar='SERVICE', help='List services on a host or cluster')

args = CommandLine(parents=parser, require_host=True)
c = Config(args)
config = c.get()

if config.args.restartservice:
    service = Service(config, servicename=config.args.restartservice)
    restarter = Restarter(config, [service])
    restarter.stop()
    restarter.start()
elif config.args.disableservice:
    service = Service(config, servicename=config.args.disableservice)
    restarter = Restarter(config, [service])
    restarter.stop()
elif config.args.enableservice:
    service = Service(config, servicename=config.args.enableservice)
    restarter = Restarter(config, [service])
    restarter.start()
