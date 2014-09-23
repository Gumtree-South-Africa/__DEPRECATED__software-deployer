import sys
import yaml
import logging
from deployerlib.config import *
from deployerlib.log import *

log = Log(instance='config_test', level=logging.DEBUG)
config_file = sys.argv[1]
log.info('Testing config "%s"' % config_file)
config = Config(config_file)
print config.dump()

keys_list = ['ams01-frontend','hosts']
value = config.get(keys_list)
print(keys_list)
print(yaml.dump(value, default_flow_style=False, indent=2))

keys_list = ['services', 'nl.marktplaats.advertisementhub.advertisementhub-server']
value = config.get(keys_list)
print(keys_list)
print(yaml.dump(value, default_flow_style=False, indent=2))

keys_list = ['something', 'nl.marktplaats.advertisementhub.advertisementhub-server']
value = config.get(keys_list)
print(keys_list)
print(yaml.dump(value, default_flow_style=False, indent=2))

keys_list = ['services', 'marktplaats.advertisementhub.advertisementhub-server']
value = config.get(keys_list)
print(keys_list)
print(yaml.dump(value, default_flow_style=False, indent=2))


