#! /usr/bin/python

import sys
import yaml
import logging
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.log import Log

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
    print(yaml.dump(value, stream=sys.stdout, default_flow_style=False, indent=2))
    print 'end'

log = Log(instance='config_test', level=logging.DEBUG)
args = CommandLine()
#print dir(args)
#print vars(args)
config = Config(args).get()
#print vars(config)
mydump(config)
#"""
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
ct_dump_by_adict_key(config,'services.advertisementhub.name')
ct_dump_by_adict_key(config,'services.advertisementlifecycle.type')
ct_dump_by_adict_key(config,'services.advertisementlifecycle.type')
ct_dump_by_adict_key(config,'args.component')

print config.service_defaults.check.handlers.http.format(**config.services.advertisementhub)
#"""
