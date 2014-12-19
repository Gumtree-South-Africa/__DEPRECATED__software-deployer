import os

from deployerlib.command import Command
from deployerlib.exceptions import DeployerException


class CleanUp(Command):
    """Clean up files named 'filespec' in the directory 'path'"""

    def initialize(self, remote_host, path, filespec, keepversions, currentversion=''):
        return True

    def execute(self):
        res = self.remote_host.execute_remote(
          "/bin/ls -1td {0}".format(os.path.join(self.path, self.filespec)))

        if res.failed:
            self.log.critical('Failed to list files in {0}: {1}'.format(self.path, res))
            return False

        files = res.split()

        if not files:
            self.log.warning('No files found in {0} with pattern {1}'.format(
              self.path, self.filespec))
            return True

        if hasattr(self, 'currentversion') and self.currentversion:
            files = [f for f in files if self.currentversion not in f]

        if not files or len(files) < self.keepversions:
            self.log.debug('No old versions to clean up')
            return True

        cleanup_files = files[self.keepversions:]

        for file in cleanup_files:
            self.log.info('Cleaning up old version: {0}'.format(file))
            res = self.remote_host.execute_remote('rm -rf {0}'.format(file))

            if res.failed:
                self.log.critical('Failed to remove {0}: {1}'.format(file, res))
                return False

        return True
