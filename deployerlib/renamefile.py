from deployerlib.log import Log
from deployerlib.fabrichelper import FabricHelper
from deployerlib.exceptions import DeployerException


class RenameFile(object):
    """Rename a remote file or directory"""


    def __init__(self, config, old_file, new_file, host, clobber=True):
        """If clobber is True, remove the target file if it exists"""

        self.log = Log(self.__class__.__name__, config=config)

        self.old_file = old_file
        self.new_file = new_file
        self.clobber = clobber

        self.fabrichelper = FabricHelper(config.general.user, host, caller=self.__class__.__name__)

    def rename(self, clobber=True):
        """Rename a remote file or directory"""

        if self.fabrichelper.file_exists(self.new_file):
            if self.clobber:
                self.log.info('Removing {0}'.format(self.new_file))
                res = self.fabrichelper.execute_remote('/bin/rm -rf {0}'.format(self.new_file))

                if not res.succeeded:
                    self.log.critical('Failed to remove {0}: {1}'.format(
                      self.new_file, res))
                    return res.succeeded
            else:
                self.log.critical('Unable to rename {0} to {1}: target already exists'.format(
                  self.old_file, self.new_file))
                return False

        self.log.debug('Renaming {0} to {1}'.format(self.old_file, self.new_file))
        res = self.fabrichelper.execute_remote('mv {0} {1}'.format(self.old_file, self.new_file))
        return res.succeeded
