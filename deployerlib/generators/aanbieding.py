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
        self.dbmigrations_stage(packages, migration_path_suffix='db/migrations')
        self.templates_stage(packages)

        if self.config.release:

            if self.config.get('graphite') and not self.tasklist.is_empty():
                self.use_graphite()

            if self.config.get('history'):
                self.archive_stage()

            if self.config.get('deploy_monitor_url'):
                self.use_deploy_monitor(self.release_version, self.config.environment)

        return self.tasklist.generate()


    def use_deploy_monitor(self, release_version, environment):
        self.deploy_monitor_notify('deploying', release_version)
        self.deploy_monitor_notify('deployed', release_version)


    def deploy_monitor_notify(self, status, release_version):
        self.log.info('Creating task for: notify deployment monitor with status {0} for {1}'.format(status, release_version))

        deploy_monitor_url = self.config.get('deploy_monitor_url')

        stage_name = 'Pipeline notify {0}'.format(status)
        self.tasklist.create_stage(stage_name)
        self.tasklist.add(stage_name, {
            'command': 'deploymonitor_notify',
            'url': deploy_monitor_url,
            'release_version': release_version,
            'environment':self.config.get('environment'),
            'status': status,
            'proxy': self.config.get('proxy'),
        })
