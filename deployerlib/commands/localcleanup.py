import os
import fnmatch
import shutil
import subprocess

from deployerlib.command import Command


class LocalCleanUp(Command):
    """Clean up files named 'filespec' in the directory 'path'"""

    def initialize(self, path, filespec, keepversions, exclude=''):
        self.exclude = exclude
        self.log.tag += '::{0}'.format(path)
        return True

    def execute(self):
        files = None
        try:
            files = sorted(os.listdir(self.path))
        except OSError as e:
            self.log.debug('Failed to list path for cleanup: {0}'.format(e))
            return True

        if not files:
            self.log.debug('No files found to cleanup')
            return True

        if self.exclude:
            self.log.debug('excluding files matching pattern {0}'.format(repr(self.exclude)))
            files = [f for f in files if not fnmatch.fnmatch(f, self.exclude)]
        elif self.keepversions < 1:
            self.log.warning('keepversions is {0}, less than 1 and exclude is not set. Setting keepversions to 1'.format(self.keepversions))
            self.keepversions = 1

        if not files or len(files) <= self.keepversions:
            self.log.debug('No old versions to clean up')
            return True

        cleanup_files = files[self.keepversions:]

        for filename in cleanup_files:
            self.log.info('Cleaning up old version: {0}'.format(filename))
            #Add check if file is a directory
            fpath = "%s" % os.path.join(self.path, filename)
            if os.path.isdir(fpath):
                shutil.rmtree(fpath)
            else: # assume its a file
                os.remove(fpath)

        return True
