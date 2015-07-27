import os
import urllib2

from deployerlib.log import Log
from deployerlib.generator import Generator
from deployerlib.exceptions import DeployerException


class AuroraGenerator(Generator):
    """Aurora task list generator"""

    def generate(self):
        """Build the task list"""

        packages = self.get_packages()

        if not self.config.redeploy:
            self.use_remote_versions(packages)

        properties_packages = [x for x in packages if x.servicename.endswith('-properties')]
        packages = [x for x in packages if not x in properties_packages]

        self.deploy_properties(properties_packages)
        self.deploy_ordered_packages(packages, self.config.deployment_order)
        self.dbmigrations_stage(packages, migration_path_suffix='db/migrations')

        # Additional stages required when doing a full release
        if self.config.release and not self.tasklist.is_empty():
            self.archive_stage()

            if self.config.get('graphite'):
                self.use_graphite()

            if self.config.get('pipeline_url'):
                release_version = os.path.basename(self.config.release[0]).replace('{0}-'.format(self.config.platform), '')
                upload = self.config.environment == 'dev'
                self.use_pipeline(release_version, upload)

        return self.tasklist.generate()
