from deployerlib.log import Log
from deployerlib.generator import Generator
from deployerlib.exceptions import DeployerException


class BoltGenerator(Generator):
    """ Bolt task list generator"""

    def generate(self):
        """Build the task list"""

        packages = self.get_packages()

        if not self.config.redeploy:
            self.use_remote_versions(packages)

        properties_packages = [x for x in packages if x.servicename.endswith('-static')]
        packages = [x for x in packages if not x in properties_packages]

        self.deploy_properties(properties_packages)
        self.deploy_ordered_packages(packages, self.config.deployment_order)
        self.dbmigrations_stage(packages, migration_path_suffix='migrations')
        self.templates_stage(packages)

        if self.config.release or self.config.component:

            if self.config.get('graphite') and not self.tasklist.is_empty():
                self.use_graphite()

            if self.config.get('write_version') and not self.tasklist.is_empty():
                self.write_version(packages[0].version)

        return self.tasklist.generate()

    def write_version(self, version):
        """Write the version to a file"""

        stage_name = 'Write version to file'
        self.tasklist.create_stage(stage_name)
        self.tasklist.add(stage_name, {
          'command': 'write_local_file',
          'filename': self.config['write_version'],
          'content': version,
        })
