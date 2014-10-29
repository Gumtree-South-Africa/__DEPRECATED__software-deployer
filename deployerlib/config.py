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
        if type(item) is str and re.search('^[a-zA-Z][a-zA-Z0-9_]*$', item):
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
                self.log.debug('No values for {0} found in config[{1}]. Will return defaults only.'.format(key,configtype))
        else:
            self.log.debug('No key "{0}" found in config. Will return defaults only.'.format(configtype))
        return AttrDict(dict(self.get_defaults(configtype)))

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

        self.log.debug('Returning {0} with username {1} and password'.format(lb_hostname, lb_username))
        return lb_hostname, lb_username, lb_password

    def get_service_hosts(self, servicename):
        """Get the list of hosts this service should be deployed to"""

        service_config = self.get_with_defaults('service', servicename)
        hosts = []

        if 'hostgroups' in service_config:
            for hg in service_config.hostgroups:
                hosts += self.hostgroup[hg]['hosts']

        if hosts:
            self.log.info('{0} is configured to run on: {1}'.format(servicename, ', '.join(hosts)))

        return hosts

    def vrfy_w_recurse(self, config, struct, parent=''):
        for item in config.keys():
            if parent:
                item_display = parent + '[{0}]'.format(item)
            else:
                item_display = item
            found = ''
            for struct_key in struct.keys():
                pattern = '^re/(.*)/$'
                m = re.findall(pattern,struct_key)
                if len(m) > 0:
                    for mp in m:
                        if re.search(mp,item):
                            found = struct_key
                else:
                    if item == struct_key:
                        found = struct_key
            if found:
                self.log.debug('Item "{0}" found in struct'.format(item_display))
                c = struct[found]
                v = config[item]
                if parent and type(v) is dict:
                    self.log.debug('Trying to get defaults for {0} "{1}"'.format(parent,item))
                    v = dict(self.get_with_defaults(parent,item).items())
                if 'type' not in c:
                    self.log.error('Struct for item "{0}" does not contain a type specification'.format(item_display))
                else:
                    if type(v) == c['type']:
                        self.log.debug('Type "{1}" of item "{0}" is correct'.format(item_display,str(c['type'])))
                        if type(v) is int:
                            if 'allowed_range' in c:
                                min,max = c['allowed_range']
                                if v >= min and v <= max:
                                    self.log.debug('Value "{1}" of item "{0}" lies within allowed range {2}'.format(item_display,v,str(c['allowed_range'])))
                                else:
                                    self.log.error('Value "{1}" of item "{0}" lies outside allowed range {2}'.format(item_display,v,str(c['allowed_range'])))
                        if type(v) is str:
                            if 'allowed_re' in c:
                                if re.match(c['allowed_re'],v):
                                    self.log.debug('Value "{1}" of item "{0}" matches RE "{2}"'.format(item_display,v,c['allowed_re']))
                                else:
                                    self.log.error('Value "{1}" of item "{0}" does NOT match RE "{2}"'.format(item_display,v,c['allowed_re']))
                        if type(v) is list:
                            if 'allowed_values' in c:
                                for va in v:
                                    if va in c['allowed_values']:
                                        self.log.debug('Member value "{1}" of list item "{0}" is allowed'.format(item_display,va))
                                    else:
                                        self.log.error('Member value "{1}" of list item "{0}" is NOT allowed'.format(item_display,va))
                            elif 'allowed_types' in c:
                                i = 0
                                for va in v:
                                    if type(va) in c['allowed_types']:
                                        allowed_struct = dict(c.items())
                                        if type(va) is not list:
                                            allowed_struct['type'] = type(va)
                                        self.vrfy_w_recurse({ '{0}[{1}]'.format(item,i): va }, { '{0}[{1}]'.format(item,i): allowed_struct })
                                    else:
                                        self.log.error('Type {0} of list member {1} of item {2} is not allowed'.format(type(va),str(va),item_display))
                                    i += 1
                        if type(v) is dict:
                            if 'allowed_struct' in c:
                                if parent:
                                    item = parent + '[{0}]'.format(item)
                                self.vrfy_w_recurse(v,c['allowed_struct'],item)
                    else:
                        if type(v) is type(None) and 'options' in c and 'allow_none' in c['options']:
                            self.log.debug('Empty value for {0} is allowed'.format(item_display))
                        else:
                            self.log.error('Unexpected type "{0}" of item "{1}"'.format(type(v),item_display))
            else:
                self.log.warning('Item "{0}" NOT found in struct'.format(item_display))

    def _get_config_struct(self):
        domain_re = '^[a-zA-Z0-9]+(?:[.-]?[a-zA-Z0-9]+)+$'
        path_re = '^[a-zA-Z0-9_/.-]+$'
        alnum_re = '^[a-zA-Z0-9_]+$'
        simple_re = '^[a-zA-Z0-9_-]+$'
        service_re = '^[a-zA-Z0-9._-]+$'
        control_type_re = '^(daemontools|apache2|tomcat|props)$'
        hostgroup_re = '^[a-z0-9]+_[a-z0-9_]+$'
        command_re = '^[^;]+$'
        username_re = '^[a-z0-9_]+$'

        service_params_struct = {
                'protocol': {
                    'type': str,
                    'allowed_re': '^(http|thrift)$',
                    },
                'destination': {
                    'type': str,
                    'allowed_re': path_re,
                    },
                'install_location': {
                    'type': str,
                    'allowed_re': path_re,
                    },
                'unpack_dir': {
                    'type': str,
                    'allowed_re': path_re,
                    },
                'control_type': {
                    'type': str,
                    'allowed_re': control_type_re,
                    },
                're/^[a-zA-Z_]+_command/': {
                    'type': str,
                    'allowed_re': command_re,
                    },
                'startup_try_count': {
                    'type': int,
                    'allowed_range': (1,100),
                    },
                'hostgroups': {
                    'type': list,
                    'allowed_types': [str],
                    'allowed_re': hostgroup_re,
                    },
                }

        lb_params_struct = {
            'api_user': {
                    'type': str,
                    'allowed_re': username_re,
                },
            'api_password': {
                'type': str,
                },
            }

        hostgroup_struct = {
                'hosts': {
                    'type': list,
                    'allowed_types': [str],
                    'allowed_re': domain_re,
                    },
                'lb': {
                    'type': str,
                    'allowed_re': domain_re,
                    },
                'defaults': {
                    'type': str,
                    'allowed_re': alnum_re,
                    },
                }

        config_structure = {
                'config': {
                    'type': str,
                    'allowed_re': path_re,
                    },
                'cluster': {
                    'type': str,
                    'allowed_re': alnum_re,
                    'options': ['allow_none'],
                    },
                'debug': {
                    'type': bool,
                    'options': ['allow_none'],
                    },
                'host': {
                    'type': str,
                    'allowed_re': domain_re,
                    'options': ['allow_none'],
                    },
                'parallel': {
                    'type': int,
                    'allowed_range': (0,30),
                    },
                'redeploy': {
                    'type': bool,
                    'options': ['allow_none'],
                    },
                'verbose': {
                    'type': bool,
                    'options': ['allow_none'],
                    },
                'dns_suffix': {
                    'type': str,
                    'allowed_re': domain_re,
                    },
                'platform': {
                    'type': str,
                    'allowed_re': alnum_re,
                    },
                'environment': {
                    'type': str,
                    'allowed_re': alnum_re,
                    },
                'keepversions': {
                    'type': int,
                    'allowed_range': (0,100),
                    },
                'logs': {
                    'type': str,
                    'allowed_re': path_re,
                    },
                'tarballs': {
                    'type': str,
                    'allowed_re': path_re,
                    },
                'graphite': {
                    'type': dict,
                    'allowed_struct': {
                        'carbon_host': {
                            'type': str,
                            'allowed_re': domain_re,
                            },
                        'carbon_port': {
                            'type': int,
                            'allowed_range': (1,65535),
                            },
                        'metric_prefix': {
                            'type': str,
                            'allowed_re': domain_re,
                            },
                        },
                    },
                'history': {
                        'type': dict,
                        'allowed_struct': {
                            'archivedir': {
                                'type': str,
                                'allowed_re': path_re,
                                },
                            'depth': {
                                'type': int,
                                'allowed_range': (1,10000),
                                },
                            },
                        },
                'user': {
                        'type': str,
                        'allowed_re': simple_re,
                        },
                'deployment_order': {
                        'type': list,
                        'allowed_types': [str,list],
                        'allowed_re': service_re,
                        },
                'datacenters': {
                        'type': list,
                        'allowed_types': [str],
                        'allowed_re': simple_re,
                        },
                'hostgroup': {
                        'type': dict,
                        'allowed_struct': {
                            're/'+hostgroup_re+'/': {
                                'type': dict,
                                'allowed_struct': dict(hostgroup_struct.items() + lb_params_struct.items()),
                                },
                            },
                        },
                're/^[a-zA-Z][a-zA-Z0-9_]*_defaults$/': {
                        'type': dict,
                        'allowed_struct': dict(service_params_struct.items() + lb_params_struct.items()),
                        },
                'service': {
                        'type': dict,
                        'allowed_struct': {
                            're/'+service_re+'/': {
                                'type': dict,
                                'allowed_struct': dict(service_params_struct.items() + lb_params_struct.items() + [
                                        ('re/^j?port$/', {
                                            'type': int,
                                            'allowed_range': (1,65535),
                                            'options': ['allow_none'],
                                            }),
                                        ('service_type', {
                                            'type': str,
                                            'allowed_re': '^[a-z_]+$'
                                            }),
                                        ]),
                                },
                            },
                        },
                }
        return config_structure


