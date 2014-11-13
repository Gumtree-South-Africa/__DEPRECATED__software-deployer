from deployerlib.command import Command
from deployerlib.exceptions import DeployerException


class CleanUp(Command):
    """Clean up files named 'filespec' in the directory 'path'"""

    def initialize(self, remote_host, path, filespec, keepversions, splitters=['_', '-']):
        self.splitters = splitters
        return True

    def split_recursive(self, s, splitters):

        for splitter in splitters:
            s = s.split(splitter)[-1]

        return s

    def execute(self):
        res = self.remote_host.execute_remote(
          "find {0} -maxdepth 1 -name '{1}'".format(self.path, self.filespec))

        if res.failed:
            self.log.critical('Failed to list files in {0}: {1}'.format(self.path, res))
            return False

        files = res.splitlines()

        if not files:
            self.log.warning('No files found in {0} with pattern {1}'.format(
              self.path, self.filespec))
            return True

        if len(files) < self.keepversions:
            self.log.debug('No old versions to clean up')
            return True

        files.sort(key=lambda x: self.split_recursive(x, self.splitters), reverse=True)

        cleanup_files = files[self.keepversions:]

        for file in cleanup_files:
            self.log.info('Cleaning up old version: {0}'.format(file))
            res = self.remote_host.execute_remote('rm -rf {0}'.format(file))

            if res.failed:
                self.log.critical('Failed to remove {0}: {1}'.format(file, res))
                return False

        return True
