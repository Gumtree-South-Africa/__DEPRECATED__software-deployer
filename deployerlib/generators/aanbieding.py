import os
import urllib2

from deployerlib.log import Log
from deployerlib.generator import Generator
from deployerlib.exceptions import DeployerException


class AanbiedingGenerator(Generator):
    """ Aanbieding task list generator"""

    def generate(self):
        """Build the task list"""

        packages = self.get_packages()

        if not self.config.redeploy:
            self.use_remote_versions(packages)

        properties_packages = [x for x in packages if x.servicename.endswith('-properties')]
        packages = [x for x in packages if not x in properties_packages]

        self.deploy_properties(properties_packages)
        #not yet enabled for aurora#self.daemontools_stage(packages)
        self.deploy_ordered_packages(packages, self.config.deployment_order)
        self.dbmigrations_stage(packages, migration_path_suffix='migrations')
        self.templates_stage(packages)

        if self.config.release:

            if self.config.get('graphite') and not self.tasklist.is_empty():
                self.use_graphite()

            if self.config.get('history'):
                self.archive_stage()

        return self.tasklist.generate()
