import os
from deployerlib.command import Command


class SymLink(Command):
    """Manage a remote symlink"""

    def initialize(self, remote_host, source, destination):
        return True

    def execute(self):
        # make sure link target is relative if dest_dir and src_dir are the same
        dest_dir = os.path.dirname(self.destination)
        src_dir  = os.path.dirname(self.source)
        if src_dir and src_dir == dest_dir:
            source = os.path.basename(self.source)
        else:
            source = self.source

        if source[0] == '/':
            src_path = source
        else:
            src_path = os.path.join(dest_dir, source)

        # check if src_path exists on remote_host
        self.log.debug('Checking if link target {0} exists'.format(src_path))
        res = self.remote_host.execute_remote('/bin/ls -d {0}'.format(src_path))

        if res.succeeded:
            if res == src_path:
                self.log.debug('Link target {0} exists'.format(src_path))
            else:
                self.log.critical("Remote command succeeded but output '{0}' is not equal to expected '{1}'".format(res, src_path))
                return False
        else:
            self.log.critical('Failed to find link target {0}: {1}'.format(src_path, res))
            return False


        self.log.debug('Checking for an existing link {0}'.format(self.destination))
        res = self.remote_host.execute_remote('/bin/readlink {0}'.format(self.destination))

        if res.succeeded:
            if res == source:
                self.log.info('Symlink {0} already points to {1}'.format(self.destination, source))
                return True
            else:
                self.log.debug('Removing old symlink: {0}'.format(self.destination))
                res = self.remote_host.execute_remote('rm {0}'.format(self.destination))

                if res.failed:
                    self.log.critical('Unable to remove old symlink {0}: {1}'.format(
                      self.destination, res))
                    return False
        else:
            self.log.debug('Symlink is not yet in place: {0}'.format(self.destination))

        self.log.info('Creating symlink {0} pointing to {1}'.format(self.destination, source))
        res = self.remote_host.execute_remote('ln -s {0} {1}'.format(
          source, self.destination))

        if res.failed:
            self.log.critical('Failed to symlink {0} to {1}: {2}'.format(
              source, self.destination, res))
            return False

        if not self.remote_host.file_exists(self.destination):
            self.log.critical('Symlink to {0} failed: {1} was not created'.format(
              source, self.destination))
            return False

        return res.succeeded
