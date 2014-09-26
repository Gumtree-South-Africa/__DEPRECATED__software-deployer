#! /usr/bin/python

import sys
import yaml
import logging
from deployerlib.config import *
from deployerlib.log import *

def ct_dump_by_keys_list(c,keys_list):
    value = c.get(keys_list)
    print(keys_list)
    print(yaml.dump(value, default_flow_style=False, indent=2))

def ct_dump_by_adict_key(c,key):
    value = eval('c.conf_adict.'+key)
    print(key)
    print(yaml.dump(value, default_flow_style=False, indent=2))

log = Log(instance='config_test', level=logging.DEBUG)
config_file = sys.argv[1]
log.info('Testing config "%s"' % config_file)
config = Config(config_file)
#print config.dump()
#print config.adump()

ct_dump_by_keys_list(config,['datacenters','dc2','names'])
ct_dump_by_keys_list(config,['services', 'nl.marktplaats.advertisementhub.advertisementhub-server'])
ct_dump_by_keys_list(config,['something', 'nl.marktplaats.advertisementhub.advertisementhub-server'])
ct_dump_by_keys_list(config,['services', 'advertisementhub-server'])


ct_dump_by_adict_key(config,'datacenters.dc2.names')
