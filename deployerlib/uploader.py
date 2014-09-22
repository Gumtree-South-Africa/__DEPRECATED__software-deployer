import os
import logging

from deployerlib.exceptions import DeployerException

class Uploader(object):
    """Upload files to a server"""

    def __init__(self, fabrichelper, service, hosts, pool_size=10, redeploy=False):
        self.fabrichelper = fabrichelper
        self.service = service
        self.hosts = hosts
        self.redeploy = redeploy
        self.pool_size = pool_size

        self.target_hosts = self.get_upload_hosts(os.path.join(self.service.upload_location, self.service.filename))

    def get_upload_hosts(self, target_file):
        """Get the list of hosts to which the package should be uploaded"""

        if self.redeploy:
            return self.hosts

        res = self.fabrichelper.file_exists(target_file, hosts=self.hosts)

        target_hosts = [host for host in res if not res[host]]
        skip_hosts = [host for host in res if not host in target_hosts]

        if skip_hosts:
            logging.debug('Package {0} already exists on hosts: {1}'.format(self.service.filename,
              ', '.join(skip_hosts)))

        logging.debug('Upload target hosts: {0}'.format(', '.join(target_hosts)))

        return target_hosts


    def upload(self):
        """Upload files to a server"""

        if not self.target_hosts:
            logging.info('{0} is not needed on any hosts'.format(self.service.filename))
            return True

        logging.debug('Uploading {0} to {1} on {2}'.format(
          self.service.fullpath, self.service.upload_location, ', '.join(self.target_hosts)))

        res = self.fabrichelper.put_remote(self.service.fullpath, self.service.upload_location,
          hosts=self.target_hosts, pool_size=self.pool_size)

        self.succeeded = [x for x in res.keys() if res[x]]
        self.failed = [x for x in res.keys() if not x in self.succeeded]

        logging.info('Uploaded {0} to {1} hosts'.format(self.service.servicename, len(self.succeeded)))

        if self.succeeded:
            logging.debug('Uploaded to hosts: {0}'.format(', '.join(self.succeeded)))

        if self.failed:
            logging.critical('Failed to upload to {0} hosts: {1}'.format(len(self.failed), ', '.join(self.failed)))

        return not self.failed
