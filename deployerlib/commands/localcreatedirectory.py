from deployerlib.command import Command

import shutil
import os


class LocalCreateDirectory(Command):
    """Create a directory on this local host"""

    def initialize(self, source, clobber=False):
        self.clobber = clobber
        return True

    def execute(self):
        """Create the directory"""
        if os.path.exists(self.source):
            if self.clobber:
                self.log.info('Removing directory {0}'.format(self.source))
                try:
                    shutil.rmtree(self.source)
                except:
                    self.log.critical('Failed to remove {0}'.format(self.source))
                    return False

            else:
                self.log.info('Directory already exists: {0}'.format(self.source))
                return True

        self.log.info('Creating directory {0}'.format(self.source))
        try:
            os.makedirs(self.source)
        except OSError as e:
            if e.errno == 17:
                self.log.warning('Directory already exists: {0}: {1}'.format(self.source, e.strerror))
            else:
                self.log.error('Failed to create directory {0}: {1}'.format(self.source, e.strerror))
                return False

        return True
