import os
import urllib2

from deployerlib.log import Log
from deployerlib.generator import Generator
from deployerlib.exceptions import DeployerException


class RTS2Generator(Generator):
    """ReplyTS2 task list generator"""

    def generate(self):
        """Build the task list"""

        packages = self.get_packages()

        if not self.config.redeploy:
            self.use_remote_versions(packages)

        self.deploy_ordered_packages(packages, self.config.deployment_order)
        #self.daemontools_stage(packages)
        #self.dbmigrations_stage(packages, migration_path_suffix='db/migrations')
        self.templates_stage(packages)

        if self.config.release:

            if self.config.get('graphite') and not self.tasklist.is_empty():
                self.use_graphite()

            if self.config.get('history'):
                self.archive_stage()

        return self.tasklist.generate()
