import os
import logging

from deployerlib.exceptions import DeployerException

class RemoteVersions(object):
    """Manage information about remote versions of services"""

    def __init__(self, fabrichelper, services, hosts, pool_size=10):

        self.fabrichelper = fabrichelper
        self.services = services
        self.hosts = hosts
        self.pool_size = pool_size

        self._remote_versions = self.get_remote_versions()

    def __repr__(self):
        """Show unambiguous representation"""
        return 'RemoteVersions(services={0}, hosts={1})'.format(
          repr([x.servicename for x in self.services]), repr(self.hosts))

    def get_remote_versions(self):
        """Find out which versions of this package are installed on the remote hosts"""

        remote_versions = {}

        for service in self.services:
            remote_versions[service.servicename] = {}
            remote_symlink = os.path.join(service.install_location, service.servicename)
            res = self.fabrichelper.get_symlink_target(remote_symlink, hosts=self.hosts, pool_size=self.pool_size)

            for host in self.hosts:
                if not res[host]:
                    remote_version = 0
                else:
                    base_target = os.path.basename(res[host])
                    remote_version = service.get_version_from_packagename(base_target)

                logging.debug('{0} current version on {1}: {2}'.format(service.servicename, host, remote_version))
                remote_versions[service.servicename][host] = remote_version

        return remote_versions

    def get_hosts_not_running_version(self, service_name, need_version):
        """Get a list of hosts that are not running the specified version"""

        if not service_name in self._remote_versions:
            return False

        target_hosts = [host for host in self._remote_versions[service_name] \
          if self._remote_versions[service_name][host] != need_version]

        return target_hosts
