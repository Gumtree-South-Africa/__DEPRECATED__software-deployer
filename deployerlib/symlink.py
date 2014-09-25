from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class SymLink(object):
    """Manage a remote symlink"""

    def __init__(self, fabrichelper, linkname):
        self.log = Log(self.__class__.__name__)

        self.fabrichelper = fabrichelper
        self.linkname = linkname

    def get_target(self, hosts):
        """Get the link target"""

        return self.fabrichelper.execute_remote('/bin/readlink {0}'.format(self.linkname),
          hosts=hosts, pool_size=self.pool_size)

    def set_target(self, link_target, hosts):
        """Set the link target"""

        if not hosts:
            self.log.info('Symlink {0} does not need to be changed on any hosts'.format(self.linkname))
            return

        self.log.info('Setting symlink for {0} on {1}'.format(link_target, ', '.join(hosts)))

        return self.fabrichelper.execute_remote('ln -sf {0} {1}'.format(link_target, self.linkname),
          hosts=hosts)
