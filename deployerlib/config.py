import yaml

from attrdict import AttrDict

from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.exceptions import DeployerException


class Config(AttrDict):

    def __init__(self, mapping={}, *args, **kwargs):

        if type(mapping) is CommandLine and hasattr(mapping, 'config'):

            self.__setattr__('log', Log(self.__class__.__name__, config=mapping), force=True)
            self.log.info('Loading configuration from {0}'.format(mapping.config))

            mapping = vars(mapping)

            with open(mapping['config'], 'r') as f:
                config = yaml.safe_load(f)
                mapping = dict(config.items() + mapping.items())

        super(self.__class__, self).__init__(mapping, *args, **kwargs)

    def get_lb_for_host(self, hostname):
        """Return the load balancer that controls the supplied host"""

        host_dc = None

        for datacenter in self.datacenters:

            if hostname in self[datacenter]['hosts']:
                host_dc = datacenter
                break

        if not host_dc:
            self.log.warning('Host {0} not found in configuration'.format(hostname))
            return None, None, None

        if not 'loadbalancers' in self[host_dc]:
            self.log.warning('Host {0} is in {1}, but there are no loadbalancers for this datacentre'.format(
              hostname, host_dc))
            return None, None, None

        lb_hostname = self[host_dc]['loadbalancers'].keys()[0]

        if len(self[host_dc]['loadbalancers'].keys()) > 1:
            self.log.warning('More than one load balancer found for {0}, using the first one ({1})'.format(
              hostname, lb))

        return (lb_hostname, self[host_dc]['loadbalancers'][lb_hostname]['username'],
          self[host_dc]['loadbalancers'][lb_hostname]['password'])
