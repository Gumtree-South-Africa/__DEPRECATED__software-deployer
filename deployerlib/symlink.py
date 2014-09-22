import logging

from deployerlib.exceptions import DeployerException


class SymLink(object):
    """Manage a remote symlink"""

    def __init__(self, fabrichelper, linkname, pool_size=3):
        self.fabrichelper = fabrichelper
        self.linkname = linkname
        self.pool_size = pool_size

    def get_target(self, hosts):
        """Get the link target"""

        return self.fabrichelper.execute_remote('/bin/readlink {0}'.format(self.linkname),
          hosts=hosts, pool_size=self.pool_size)

    def set_target(self, link_target, hosts):
        """Set the link target"""

        if not hosts:
            logging.info('Symlink {0} does not need to be changed on any hosts'.format(self.linkname))
            return

        logging.info('Setting symlink for {0} on {1}'.format(link_target, ', '.join(hosts)))

        return self.fabrichelper.execute_remote('ln -sf {0} {1}'.format(link_target, self.linkname),
          hosts=hosts, pool_size=self.pool_size)
