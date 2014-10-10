#! /usr/bin/python

import sys
import argparse
import yaml
from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.exceptions import DeployerException

def ct_dump_by_keys_list(c,keys_list):
    index_str = 'c'
    for k in keys_list:
        index_str += "['" + k + "']"
    print(keys_list)
    print('value = '+index_str)
    try:
        value = eval(index_str)
        mydump(value)
    except Exception, e:
        print 'Not found in config'

def ct_dump_by_adict_key(c,key):
    value = eval('c.'+key)
    print(key)
    print('value = c.'+key)
    mydump(value)

def mydump(value):
    print value
    print yaml.dump(value, default_flow_style=False, indent=2)

def print_configs(config, configtype, name):
    print
    print '=> config.{0}["{1}"]:'.format(configtype, name)
    try:
        mydump(eval('config.' + configtype + '[name]'))
    except Exception, e:
        print e

    print
    print "=> config.get_with_defaults('{0}', '{1}'):".format(configtype,name)
    mydump(config.get_with_defaults(configtype, name))

def print_service_configs(config, servicename):
    print_configs(config, 'service', servicename)

log = Log('config_test')

# Add command line option for components to deploy
parser = argparse.ArgumentParser()
parser.add_argument('--servicename', help='Specify the service name to act on', required=True)

args = CommandLine(parents=parser)
config = Config(args)

print
print '=> config:'
print(vars(config))

print
print '=> config.user:'
mydump(config.user)

print
print '=> config.service:'
mydump(config.service)

print
print '=> config.get_defaults("service")'
print config.get_defaults('service')

if config.servicename == 'all':
    for servicename in config.service.keys():
        print_service_configs(config, servicename)
else:
    print_service_configs(config, config.servicename)
    x = config.get_with_defaults('service', config.servicename)
    mydump(x)

"""
print
print '=> non existing service:'
print_service_configs(config, 'some-non-existent')

print
print '=> non existing config type:'
mydump(config.get_with_defaults('nonexistent','something'))

print
print '=> datacenters:'
mydump(config.datacenters)

print
print '=> lb config:'
mydump(config.lb)

print
print '=> lb belb001.dro config with defaults:'
print_configs(config, 'lb', 'belb001.dro')

print
print '=> hostgroups with defaults:'
for hg in config.hostgroup.keys():
    print_configs(config, 'hostgroup', hg)

args = CommandLine()
#print dir(args)
#print vars(args)
config = Config(args).get()
#print vars(config)
mydump(config)

#config_file = sys.argv[1]
#log.info('Testing config "%s"' % config_file)
#config = Config(config_file)
#print config.adump()

ct_dump_by_keys_list(config,['datacenters','dc2','names'])
ct_dump_by_keys_list(config,['services', 'nl.marktplaats.advertisementhub.advertisementhub-server'])
ct_dump_by_keys_list(config,['something', 'nl.marktplaats.advertisementhub.advertisementhub-server'])
ct_dump_by_keys_list(config,['services', 'advertisementhub-server'])


ct_dump_by_adict_key(config,'general.dns_suffix')
ct_dump_by_adict_key(config,'datacenters.dc2.names')
ct_dump_by_adict_key(config,'dc2.hosts')
ct_dump_by_adict_key(config,'services')
ct_dump_by_adict_key(config,'services.advertisementlifecycle.type')
ct_dump_by_adict_key(config,'services.advertisementlifecycle.type')
ct_dump_by_adict_key(config,'args.component')

print config.service_defaults.check.handlers.http.format(**config.services.advertisementhub)
"""
