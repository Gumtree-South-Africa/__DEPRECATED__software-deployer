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

        if not self.tasklist.is_empty():
            if self.config.release:
                release_version = os.path.basename(self.config.release[0]).replace('{0}-'.format(self.config.platform), '')
                deployment_type = 'release'
                deploy_items = release_version

                if self.config.get('history'):
                    self.archive_stage()

                if self.config.get('graphite'):
                    self.use_graphite()

                if self.config.get('pipeline_url'):
                    upload = self.config.environment == 'dev'
                    self.use_pipeline(release_version, upload)

            elif self.config.get('component'):
                deployment_type = 'components'
                deploy_items = ','.join([os.path.basename(x) for x in self.config.component])

            else:
                deployment_type = 'unknown_type'
                deploy_items = 'unknown'

        else:
            deployment_type = 'empty'
            deploy_items = 'none'

        return self.tasklist.generate('Deployment of platform {0}, environment {1}, {2} {3}'.format(self.config.platform, self.config.environment,
            deployment_type, repr(deploy_items)))
