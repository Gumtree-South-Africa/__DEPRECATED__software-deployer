import os

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class RemoteVersions(object):
    """Manage information about remote versions of services"""

    def __init__(self, fabrichelper, services, pool_size=10):
        self.log = Log(self.__class__.__name__)

        self.fabrichelper = fabrichelper
        self.services = services
        self.pool_size = pool_size

        self._remote_versions = self._get_remote_versions()

    def __repr__(self):
        """Show unambiguous representation"""
        return '{0}(services={1})'.format(self.__class__.__name__,
          repr([x.servicename for x in self.services]))

    def _get_remote_versions(self):
        """Find out which versions of this package are installed on the remote hosts"""

        remote_versions = {}

        for service in self.services:
            remote_versions[service.servicename] = {}
            remote_symlink = os.path.join(service.install_location, service.servicename)
            res = self.fabrichelper.execute_remote('/bin/readlink {0}'.format(remote_symlink),
              hosts=service.hosts, pool_size=self.pool_size)

            for host in service.hosts:
                if not res[host]:
                    remote_version = 0
                else:
                    base_target = os.path.basename(res[host])
                    remote_version = service.get_version_from_packagename(base_target)

                self.log.debug('{0} current version on {1}: {2}'.format(service.servicename, host, remote_version))
                remote_versions[service.servicename][host] = remote_version

        return remote_versions

    def get_hosts_running_version(self, service_name, need_version):
        """Get a list of hosts that are not running the specified version"""

        if not service_name in self._remote_versions:
            raise DeployerException('RemoteVersions: Unknown service: {0}'.format(service_name))

        target_hosts = [host for host in self._remote_versions[service_name] \
          if self._remote_versions[service_name][host] == need_version]

        return target_hosts

    def get_hosts_not_running_version(self, service_name, need_version):
        """Get a list of hosts that are not running the specified version"""

        if not service_name in self._remote_versions:
            raise DeployerException('RemoteVersions: Unknown service: {0}'.format(service_name))

        target_hosts = [host for host in self._remote_versions[service_name] \
          if self._remote_versions[service_name][host] != need_version]

        return target_hosts

    def get_host_version(self, service_name, hostname):
        """Get the version number of a service on a single host"""

        if not service_name in self._remote_versions:
            raise DeployerException('RemoteVersions: Unknown service: {0}'.format(service_name))

        if hostname in self._remote_versions[service_name]:
            return self._remote_versions[service_name]
        else:
            return None
