import os

from deployerlib.log import Log
from deployerlib.fabrichelper import FabricHelper
from deployerlib.exceptions import DeployerException


class Uploader(object):
    """Upload files to a server"""

    def __init__(self, config, service, host):
        self.log = Log(self.__class__.__name__, config=config)

        self.service = service
        self.host = host
        self.config = config
        self.upload_hosts = {}

        self.fabrichelper = FabricHelper(self.config.general.user, self.host, caller=self.__class__.__name__)

    def upload(self):
        """Upload files to a server"""

        self.log.info('Uploading {0} to {1}'.format(
          self.service.fullpath, self.host))

        res = self.fabrichelper.put_remote(self.service.fullpath, self.service.upload_location)

        if res.succeeded:
            self.log.debug('Uploaded {0} to {1} on {2}'.format(self.service.servicename,
              self.service.upload_location, self.host))

        else:
            self.log.critical('Failed to upload {0} to {1}'.format(self.service.servicename, self.host))

        return res.succeeded
