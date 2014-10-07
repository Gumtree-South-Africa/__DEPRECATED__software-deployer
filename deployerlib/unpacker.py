import os

from deployerlib.log import Log
from deployerlib.fabrichelper import FabricHelper
from deployerlib.exceptions import DeployerException


class Unpacker(object):
    """Unpack a packge on a remote host"""

    def __init__(self, config, service, host):
        self.log = Log(self.__class__.__name__)

        self.config = config
        self.service = service
        self.host = host

        self.fabrichelper = FabricHelper(self.config.general.user, self.host, caller=self.__class__.__name__)

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

    def unpack(self):
        """Unpack the remote package"""

        unpack_command = self.get_unpack_command(self.service)

        if self.fabrichelper.file_exists(self.service.install_destination):

            if self.config.args.redeploy:
                # Todo: This should not be done before stopping the service
                self.log.info('Removing {0} on {1}'.format(self.service.install_destination, self.host))
                res = self.fabrichelper.execute_remote('/bin/rm -rf {0}'.format(self.service.install_destination))

                if not res:
                    self.log.critical('Failed to remove {0}: {1}'.format(
                      self.service.install_destination, res))
                    return res

            else:
                self.log.info('{0} is already in place on {1}'.format(self.service.packagename, self.host))
                return True

        self.log.info('Unpacking {0} on {1}'.format(self.service.servicename, self.host))
        return self.fabrichelper.execute_remote(unpack_command)
