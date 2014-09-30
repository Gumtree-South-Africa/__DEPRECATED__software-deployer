import os
import sys
import yaml
from attrdict import AttrDict, load
from deployerlib.exceptions import DeployerException
from deployerlib.log import Log

class Config(object):
    """Config object class for reading config from file provided on commandline.
    The parsed args given on commandline will be part of the config object"""

    def __init__(self, args):
        log = Log('Config')
        conf_file = args.config
        log.info('Reading config from: {0}'.format(conf_file))
        self.conf_adict = load(conf_file, load_function=yaml.safe_load)
        self.conf_adict.args = AttrDict()
        for k,v in args.iteritems():
            self.conf_adict.args[k] = v

    def get(self):
        return self.conf_adict
