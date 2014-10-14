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
#parser.add_argument('--steps', nargs='*', default=[disable_loadbalancer, stop_service, start_service, enable_loadbalancer],
#  help='List of deployment steps to perform')

args = CommandLine(parents=parser, require_host=True)
config = Config(args)

if config.restartservice:
    config.steps = ['disable_loadbalancer', 'stop_service', 'start_service', 'enable_loadbalancer']
    servicenames = config.restartservice
elif config.disableservice:
    config.steps = ['disable_loadbalancer', 'stop_service']
    servicenames = config.disableservice
elif config.enableservice:
    config.steps = ['start_service', 'enable_loadbalancer']
    servicenames = config.enableservice

services = []

for servicename in servicenames:
    services.append(Service(config, servicename=servicename))

orchestrator = Orchestrator(config, services)
orchestrator.direct_run()
