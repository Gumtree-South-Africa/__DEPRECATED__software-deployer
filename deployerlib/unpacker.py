import os
import logging

from deployerlib.exceptions import DeployerException


class Unpacker(object):
    """Unpack a packge on a remote host"""

    def __init__(self, fabrichelper, service, hosts, pool_size=3, redeploy=False):
        self.fabrichelper = fabrichelper
        self.service = service
        self.hosts = hosts
        self.pool_size = pool_size
        self.redeploy = redeploy

        self.unpack_command = self.get_unpack_command()
        self.target_hosts = self.get_target_hosts()

        logging.debug('All hosts: {0}; Target hosts: {1}'.format(
          ', '.join(self.hosts), ', '.join(self.target_hosts)))

    def get_unpack_command(self):
        """Based on the package type, determine the command line to unpack the package"""

        target_file = os.path.join(self.service.upload_location, self.service.filename)

        if self.service.filetype == 'tar':
            command_line = '/bin/tar zxf {0} -C {1}'.format(target_file, self.service.install_location)
        elif self.service.filtype == 'war':
            command_line = '/bin/cp {0} {1}'.format(target_file, self.service.install_location)
        else:
            raise DeployerException('{0}: Unpacker doesn\'t know how to unpack filetype: {1}'.format(
              self.service.servicename, self.service.filetype))

        logging.debug('unpack_command for {0} is {1}'.format(
          self.service.servicename, command_line))

        return command_line

    def get_target_hosts(self):
        """Check whether the package we're about to unpack has already been installed"""

        if not self.hosts:
            return self.hosts

        res = self.fabrichelper.file_exists(self.service.install_destination, hosts=self.hosts)

        target_hosts = [host for host in res if not res[host]]

        return target_hosts

    def unpack(self):
        """Unpack the remote package"""

        missing_targets = [host for host in self.hosts if not host in self.target_hosts]

        if missing_targets:
            logging.info('The following hosts already have {0} in place: {1}'.format(
              self.service.packagename, ', '.join(missing_targets)))

            if self.redeploy:
                logging.info('Removing {0} on {1}'.format(self.service.install_destination, ', '.join(missing_targets)))
                res = self.fabrichelper.execute_remote('/bin/rm -rf {0}'.format(self.service.install_destination), hosts=missing_targets)
                self.target_hosts = self.hosts

        if not self.target_hosts:
            logging.info('No hosts require {0} to be unpacked.'.format(self.service.servicename))
            return

        logging.info('Unpacking on {0} on hosts: {1}'.format(self.service.servicename, ', '.join(self.target_hosts)))

        self.fabrichelper.execute_remote(self.unpack_command, hosts=self.target_hosts, pool_size=self.pool_size)
