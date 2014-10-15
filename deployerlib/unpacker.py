import os

from deployerlib.log import Log
from deployerlib.fabrichelper import FabricHelper
from deployerlib.exceptions import DeployerException


class Unpacker(object):
    """Unpack a packge on a remote host"""

    def __init__(self, config, service, host, clobber=False):
        self.log = Log(self.__class__.__name__, config=config)

        self.config = config
        self.service = service
        self.host = host
        self.clobber = clobber

        if self.service.unpack_dir != self.service.install_location:
            self.clobber = True

        self.fabrichelper = FabricHelper(self.config.user, self.host, caller=self.__class__.__name__)

    def get_unpack_command(self, service):
        """Based on the package type, determine the command line to unpack the package"""

        if service.filetype == 'tar':
            command_line = '/bin/tar zxf {0} -C {1}'.format(service.remote_filename, self.service.unpack_dir)
        elif service.filetype == 'war':
            command_line = '/bin/cp {0} {1}'.format(service.remote_filename, self.service.unpack_dir)
        else:
            raise DeployerException('{0}: Unpacker doesn\'t know how to unpack filetype: {1}'.format(
              service.servicename, service.filetype))

        self.log.debug('unpack_command for {0} is: {1}'.format(
          service.servicename, command_line))

        return command_line

    def unpack(self):
        """Unpack the remote package"""

        unpack_command = self.get_unpack_command(self.service)

        if self.fabrichelper.file_exists(self.service.unpack_destination):

            if self.clobber:
                self.log.info('Removing {0}'.format(self.service.unpack_destination))
                res = self.fabrichelper.execute_remote('/bin/rm -rf {0}'.format(self.service.unpack_destination))

                if not res.succeeded:
                    self.log.critical('Failed to remove {0}: {1}'.format(
                      self.service.unpack_destination, res))
                    return res.succeeded

            else:
                self.log.info('Unable to unpack to {0}: target directory already exists'.format(self.service.unpack_destination))
                return False

        if not self.fabrichelper.file_exists(self.service.unpack_dir):
            self.log.debug('Creating directory {0}'.format(self.service.unpack_dir))
            self.fabrichelper.execute_remote('mkdir -p {0}'.format(self.service.unpack_dir))

        self.log.info('Unpacking {0}'.format(self.service.servicename))
        res = self.fabrichelper.execute_remote(unpack_command)

        if not res.succeeded:
            self.log.critical('Unpack failed: {0}'.format(res))

        return res.succeeded
