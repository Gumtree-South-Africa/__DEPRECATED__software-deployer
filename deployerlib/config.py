import yaml
import re

from attrdict import AttrDict

from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.exceptions import DeployerException


class Config(AttrDict):

    def __init__(self, mapping={}, *args, **kwargs):

        if type(mapping) is CommandLine and hasattr(mapping, 'config'):

            self.__setattr__('log', Log(self.__class__.__name__), force=True)
            self.log.info('Loading configuration from {0}'.format(mapping.config))

            mapping = vars(mapping)

            with open(mapping['config'], 'r') as f:
                config = yaml.safe_load(f)
                mapping = dict(config.items() + mapping.items())

        super(self.__class__, self).__init__(mapping, *args, **kwargs)

    def get_defaults(self, item, recurse=True):
        d = {}
        if type(item) is str and re.search('^[a-zA-Z_]+$', item):
            dkey = item + '_defaults'
            if dkey in self:
                d = dict(self[dkey].items())
                if recurse:
                    for (k,v) in dict(d).items():
                        d = dict(self.get_defaults(k) + self.get_defaults(v) + d.items())
        elif type(item) is dict:
            for (k,v) in item.items():
                d = dict(self.get_defaults(k) + self.get_defaults(v) + d.items())
        return d.items()

    def get_with_defaults(self, configtype, key):
        if configtype in self:
            if key in self[configtype]:
                c = self[configtype][key]
                ct_defaults = self.get_defaults(configtype,False)
                c_defaults = self.get_defaults(dict(c.items()))
                return AttrDict(dict(ct_defaults + c_defaults + self.get_defaults(dict(ct_defaults + c_defaults + c.items())) + c.items()))
            else:
                self.log.error('No values for {0} found in config[{1}]'.format(key,configtype))
        else:
            self.log.error('No key "{0}" found in config'.format(configtype))

    def get_lb(self, servicename, hostname):
        """Return the load balancer that controls supplied service on supplied host"""

        host_hg = None

        hostgroups =  self.get_with_defaults('service', servicename)['hostgroups']
        for hg in hostgroups:

            if hostname in self.hostgroup[hg]['hosts']:
                host_hg = hg
                break

        if not host_hg:
            self.log.warning('Host {0} not found in any hostgroups associated to {1}'.format(hostname, servicename))
            return None, None, None

        if not 'lb' in self.hostgroup[host_hg]:
            self.log.warning('Host {0} is in hostgroup {1}, but there are no loadbalancers defined for it'.format(
              hostname, host_hg))
            return None, None, None

        lb_hostname = self.hostgroup[host_hg]['lb']
        lb_config = self.get_with_defaults('lb', lb_hostname)
        lb_username = lb_config.api_user
        lb_password = lb_config.api_password

        return lb_hostname, lb_username, lb_password
