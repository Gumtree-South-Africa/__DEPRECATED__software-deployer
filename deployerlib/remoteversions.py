import os

from multiprocessing import Manager

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class RemoteVersions(object):
    """Manage information about remote versions of services"""

    def __init__(self, config):
        self.log = Log(self.__class__.__name__, config=config)

        manager = Manager()
        self._remote_versions = manager.list()

    def __repr__(self):

        return '{0}(services={1})'.format(self.__class__.__name__,
          repr([x.servicename for x in self.services]))

    def get_remote_version(self, service, host, remote_results={}, procname=None):
        """Get the version of a remote service"""

        remote_symlink = os.path.join(service.install_location, service.servicename)
        res = host.execute_remote('/bin/readlink {0}'.format(remote_symlink))

        if res:
            installed_package = os.path.basename(res)
            remote_version = service.get_version_from_packagename(installed_package)
        else:
            remote_version = 1

        self.log.debug('{0} current version is {1}'.format(service.servicename, remote_version))

        self._remote_versions.append((service.servicename, host.hostname, remote_version))

        remote_results[procname] = remote_version
        return remote_version

    def resolve_remote_versions(self):
        """Create a nested dict from the manager list
           (workaround for lack of nested manager dicts)
        """

        remote_versions = {}

        for l in self._remote_versions:
            servicename, hostname, version = l

            if not servicename in remote_versions:
                remote_versions[servicename] = {}

            remote_versions[servicename][hostname] = version

        return remote_versions
