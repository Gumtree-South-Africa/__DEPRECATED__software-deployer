from deployerlib.command import Command

import shutil
import os


class CreateDirectory(Command):
    """Create a directory on a remote or local host"""

    def initialize(self, remote_host, source, clobber=False):
        self.clobber = clobber

        return True

    def execute(self):
        """Create the directory"""
        if self.remote_host is "localhost":
            if os.path.exists(self.source):
                if self.clobber:
                    self.log.info('Removing directory {0}'.format(self.source))
                    try:
                        shutil.rmtree(self.source)
                        return True
                    except:
                        self.log.critical('Failed to remove {0}: {1}'.format(self.source, res))
                        return False

                else:
                    self.log.info('Directory already exists: {0}'.format(self.source))
                    return True

            self.log.info('Creating directory {0}'.format(self.source))
            try:
                os.makedirs(self.source)
            except OSError as e:
                if e.errno == 17:
                    self.log.warning('Directory already exists: {0}: {1}'.format(self.source, res))
                else:
                    self.log.error('Failed to create directory {0}: {1}'.format(self.source, res))
                    return False

            return True
        else:
            if self.remote_host.file_exists(self.source):

                if self.clobber:
                    self.log.info('Removing directory {0}'.format(self.source))
                    res = self.remote_host.execute_remote('rm -rf {0}'.format(self.source))

                    if not res.succeeded:
                        self.log.critical('Failed to remove {0}: {1}'.format(self.source, res))
                        return res.succeeded

                else:
                    self.log.info('Directory already exists: {0}'.format(self.source))
                    return True

            self.log.info('Creating directory {0}'.format(self.source))
            res = self.remote_host.execute_remote('mkdir -p {0}'.format(self.source))

            if not res.succeeded:
                self.log.critical('Failed to create directory {0}: {1}'.format(self.source, res))

            return res.succeeded
