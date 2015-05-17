import os
import fnmatch

from deployerlib.command import Command
from deployerlib.exceptions import DeployerException


class CleanUp(Command):
    """Clean up files named 'filespec' in the directory 'path'"""

    def initialize(self, remote_host, path, filespec, keepversions, exclude=''):
        self.exclude = exclude
        self.log.tag += '::{0}'.format(path)
        return True

    def execute(self):
        res = self.remote_host.execute_remote("/bin/ls -1Atd {0}/{1}".format(self.path, self.filespec), output_hidebug=True)

        if res.failed:
            self.log.warning('Failed to list path for cleanup: {0}'.format(res))
            return True

        files = res.split()

        if not files:
            self.log.info('No files found to cleanup')
            return True

        if self.exclude:
            self.log.debug('excluding files matching pattern {0}'.format(repr(self.exclude)))
            files = [f for f in files if not fnmatch.fnmatch(f, self.exclude)]
        elif self.keepversions < 1:
            self.log.warning('keepversions is {0}, less than 1 and exclude is not set. Setting keepversions to 1'.format(self.keepversions))
            self.keepversions = 1

        if not files or len(files) <= self.keepversions:
            self.log.info('No old versions to clean up')
            return True

        cleanup_files = files[self.keepversions:]

        for filename in cleanup_files:
            self.log.info('Cleaning up old version: {0}'.format(filename))
            res = self.remote_host.execute_remote('rm -rf {0}'.format(os.path.join(self.path, filename)))

            if res.failed:
                self.log.error('Failed to remove {0}: {1}'.format(filename, res))

        return True
