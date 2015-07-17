import os

from subprocess import check_output

from deployerlib.command import Command


class Upload(Command):
    """Upload files to a server"""

    def initialize(self, remote_host, source, destination, checksum_command='/usr/bin/md5sum'):
        """Pass checksum_command=None to skip checksum"""

        self.checksum_command = checksum_command
        return True

    def execute(self, procname=None, remote_results={}):
        """Upload files to a server"""

        # Skip upload if remote file is already in place
        if self.checksum_command:

            if self.match_checksum():
                self.log.debug('File {0} already exists in {1}'.format(self.source, self.destination))
                self.log.info('Package has already been uploaded'.format(self.source))
                return True

        self.log.info('Uploading {0}'.format(self.source))

        res = self.remote_host.put_remote(self.source, self.destination)

        if res.failed:
            self.log.critical('Failed to upload {0} to {1}:{2}: {3}'.format(
              self.source, self.remote_host.hostname, self.destination, res))
            return False

        self.log.debug('Uploaded {0} to {1} on {2}'.format(self.source,
          self.destination, self.remote_host.hostname))

        return res.succeeded

    def match_checksum(self):
        """Compare source and destination file checksums"""

        try:
            out = check_output([self.checksum_command, self.source])
        except OSError as e:
            self.log.debug('Failed to checksum local file {0}: {1}'.format(self.source, e))
            return False

        local_checksum = out.split()[0]

        remote_file = os.path.join(self.destination, os.path.basename(self.source))
        res = self.remote_host.execute_remote('{0} {1}'.format(self.checksum_command, remote_file))

        if res.failed:
            self.log.debug('Failed to checksum remote file {0}: {1}'.format(remote_file, res))
            return False

        remote_checksum = res.split()[0]

        if local_checksum == remote_checksum:
            self.log.debug('Matching checksums: {0}'.format(local_checksum))
            return True

        self.log.debug('Checksums differ: local {0}, remote {1}'.format(local_checksum, remote_checksum))
        return False
