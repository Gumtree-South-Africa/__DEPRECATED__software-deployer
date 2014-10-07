#! /usr/bin/python

import argparse

from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.service import Service
from deployerlib.orchestrator import Orchestrator

parser = argparse.ArgumentParser()
action_group = parser.add_mutually_exclusive_group(required=True)
action_group.add_argument('--restartservice', nargs='+', metavar='SERVICE', help='Single service to restart')
action_group.add_argument('--disableservice', nargs='+', metavar='SERVICE', help='Single service to disable')
action_group.add_argument('--enableservice', nargs='+', metavar='SERVICE', help='Single service to enable')
action_group.add_argument('--listservices', nargs='+', metavar='SERVICE', help='List services on a host or cluster')

args = CommandLine(parents=parser, require_host=True)
c = Config(args)
config = c.get()

if config.args.restartservice:
    config.steps = ['stop', 'start']
    servicenames = config.args.restartservice
elif config.args.disableservice:
    config.steps = ['stop']
    servicenames = config.args.disableservice
elif config.args.enableservice:
    config.steps = ['start']
    servicenames = config.args.enableservice

services = []

for servicename in servicenames:
    services.append(Service(config, servicename=servicename))

orchestrator = Orchestrator(config, services)
orchestrator.run()
