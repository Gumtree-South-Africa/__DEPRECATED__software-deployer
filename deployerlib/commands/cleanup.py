import os

from deployerlib.command import Command
from deployerlib.exceptions import DeployerException


class CleanUp(Command):
    """Clean up files named 'filespec' in the directory 'path'"""

    def initialize(self, remote_host, path, filespec, keepversions, exclude=''):
        self.exclude = exclude
        return True

    def execute(self):
        res = self.remote_host.execute_remote(
          "/bin/ls -1td {0}".format(os.path.join(self.path, self.filespec)))

        if res.failed:
            self.log.critical('{0}: Failed to list files: {1}'.format(self.path, res))
            return False

        files = res.split()

        if not files:
            self.log.warning('{0}: No files found in with pattern {1}'.format(
              self.path, self.filespec))
            return True

        if self.exclude:
            self.log.debug('{0}: excluding files matching pattern {1}'.format(self.path, repr(self.exclude)))
            files = [f for f in files if self.exclude not in f]
        elif self.keepversions < 1:
            self.log.warning('{0}: keepversions is {1}, less than 1 and exclude is not set. Setting keepversions to 1'.format(self.path, self.keepversions))
            self.keepversions = 1

        if not files or len(files) <= self.keepversions:
            self.log.debug('{0}: No old versions to clean up'.format(self.path))
            return True

        cleanup_files = files[self.keepversions:]

        for file in cleanup_files:
            self.log.info('{0}: Cleaning up old version: {1}'.format(self.path, os.path.basename(file)))
            res = self.remote_host.execute_remote('rm -rf {0}'.format(file))

            if res.failed:
                self.log.critical('{0}: Failed to remove {1}: {2}'.format(self.path, os.path.basename(file), res))
                return False

        return True
