import os
import sys
import yaml
from attrdict import AttrDict
from deployerlib.exceptions import DeployerException
from deployerlib.log import *

class Config(object):
    """Config object class for reading in configuration from file"""

    def __init__(self, conf_file):
        self.log = Log('Config')
        self.log.info('Reading config from: {0}'.format(conf_file))
        try:
            fp = open(conf_file, 'r')
            self.conf_data = yaml.load(fp)
            self.conf_adict = AttrDict(self.conf_data)
        except Exception, e:
            self.log.error(e.message)

    def get(self, keys=[]):
        """Getter for any item in conf_data, by keys_list"""
        error = False
        keys_pointer = []
        temp_data = self.conf_data
        for k in keys:
            keys_pointer.append(k)
            if type(temp_data) == type({}) and k in temp_data:
                temp_data = temp_data[k]
            else:
                error = True
                break
        if error:
            self.log.error('Could not find value for [{0}] in config'.format(', '.join(keys_pointer)))
        else:
            self.log.debug('Found value for [{0}] in config'.format(', '.join(keys)))
            return temp_data

    def dump(self, format='yaml'):
        """Dumper to return conf_data in several formats"""
        if format == 'yaml':
            return yaml.dump(self.conf_data, default_flow_style=False, indent=2)
        else:
            self.log.error('Requested format "%s" is not supported' % format)

    def adump(self, format='yaml'):
        """Dumper to return conf_data in several formats"""
        if format == 'yaml':
            return yaml.dump(self.conf_adict, default_flow_style=False, indent=2)
        else:
            self.log.error('Requested format "%s" is not supported' % format)

