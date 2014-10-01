import os

from deployerlib.log import Log
from deployerlib.fabrichelper import FabricHelper
from deployerlib.exceptions import DeployerException


class Uploader(object):
    """Upload files to a server"""

    def __init__(self, services, args, config, pool_size=10):
        self.log = Log(self.__class__.__name__)

        self.services = services
        self.args = args
        self.config = config
        self.upload_hosts = {}

        self.fabrichelper = FabricHelper(self.config.general.user, pool_size=pool_size, caller=self.__class__.__name__)

        for service in self.services:
            self.upload_hosts[service.servicename] = self.get_upload_hosts(service)

    def get_upload_hosts(self, service):
        """Get the list of hosts to which the package should be uploaded"""

        if self.args.redeploy or not service.hosts:
            return service.hosts

        res = self.fabrichelper.file_exists(service.remote_filename, hosts=service.hosts)

        target_hosts = [host for host in res if not res[host]]
        skip_hosts = [host for host in res if not host in target_hosts]

        if skip_hosts:
            self.log.debug('Package {0} already exists on hosts: {1}'.format(service.filename,
              ', '.join(skip_hosts)))

        return target_hosts

    def upload(self):
        """Upload files to a server"""

        for service in self.services:

            if self.args.redeploy:
                upload_hosts = service.hosts
            else:
                upload_hosts = self.get_upload_hosts(service)

            if not upload_hosts:
                self.log.info('{0} is not needed on any hosts'.format(service.filename))
                return

            self.log.debug('Uploading {0} to {1} on {2}'.format(
              service.fullpath, service.upload_location, ', '.join(upload_hosts)))

            res = self.fabrichelper.put_remote(service.fullpath, service.upload_location,
              hosts=upload_hosts)

            succeeded = [x for x in res.keys() if res[x]]
            failed = [x for x in res.keys() if not x in succeeded]

            self.log.info('Uploaded {0} to {1} hosts'.format(service.servicename, len(succeeded)))

            if succeeded:
                self.log.debug('Uploaded to hosts: {0}'.format(', '.join(succeeded)))

            if failed:
                self.log.critical('Failed to upload to {0} hosts: {1}'.format(len(failed), ', '.join(failed)))
