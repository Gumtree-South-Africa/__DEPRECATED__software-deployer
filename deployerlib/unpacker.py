import os

from deployerlib.log import Log
from deployerlib.fabrichelper import FabricHelper
from deployerlib.exceptions import DeployerException


class Unpacker(object):
    """Unpack a packge on a remote host"""

    def __init__(self, config, services):
        self.log = Log(self.__class__.__name__)

        self.services = services
        self.config = config

        self.fabrichelper = FabricHelper(self.config.general.user,
          pool_size=self.config.args.parallel, caller=self.__class__.__name__)

    def get_unpack_command(self, service):
        """Based on the package type, determine the command line to unpack the package"""

        if service.filetype == 'tar':
            command_line = '/bin/tar zxf {0} -C {1}'.format(service.remote_filename, service.install_location)
        elif service.filetype == 'war':
            command_line = '/bin/cp {0} {1}'.format(service.remote_filename, service.install_location)
        else:
            raise DeployerException('{0}: Unpacker doesn\'t know how to unpack filetype: {1}'.format(
              service.servicename, service.filetype))

        self.log.debug('unpack_command for {0} is: {1}'.format(
          service.servicename, command_line))

        return command_line

    def get_target_hosts(self, service):
        """Check whether the package we're about to unpack has already been installed"""

        if not service.hosts:
            return service.hosts, None

        res = self.fabrichelper.file_exists(service.install_destination, hosts=service.hosts)

        target_hosts = [host for host in res if not res[host]]
        exists_hosts = [host for host in res if not host in target_hosts]

        self.log.debug('{0} needs to be unpacked on: {1}'.format(service.servicename,
          ', '.join(target_hosts)))
        self.log.debug('{0} has already been unpacked on: {1}'.format(service.servicename,
          ', '.join(exists_hosts)))

        return target_hosts, exists_hosts

    def unpack(self):
        """Unpack the remote package"""

        for service in self.services:
            target_hosts, exists_hosts = self.get_target_hosts(service)
            unpack_command = self.get_unpack_command(service)

            if exists_hosts:
                self.log.info('The following hosts already have {0} in place: {1}'.format(
                  service.packagename, ', '.join(exists_hosts)))

                if self.config.args.redeploy:
                    # Todo: This should not be done as part of "pre_deploy" tasks
                    self.log.info('Removing {0} on {1}'.format(service.install_destination, ', '.join(exists_hosts)))
                    res = self.fabrichelper.execute_remote('/bin/rm -rf {0}'.format(service.install_destination),
                      hosts=exists_hosts)
                    target_hosts = service.hosts

            if not target_hosts:
                self.log.info('No hosts require {0} to be unpacked.'.format(service.servicename))
                continue

            self.log.info('Unpacking {0} on hosts: {1}'.format(service.servicename, ', '.join(target_hosts)))
            self.fabrichelper.execute_remote(unpack_command, hosts=target_hosts)
