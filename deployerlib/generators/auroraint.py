from deployerlib.generator import Generator


class AuroraIntGenerator(Generator):
    """Aurora integration list generator"""

    def generate(self):
        """Build the task list"""

        tasks = []

        #get them from the config
        services = []
        try:
            services=self.config.deploygroups[self.config.packagegroup]
        except KeyError:
            return []

        tasks.append({
            'command': 'createdeploypackage',
            'remote_host': self.config.remote_host,
            'packagegroup': self.config.packagegroup,
            'service_names': services,
            'destination': self.config.destination,
            'webapps_location': self.config.service_defaults.install_location,
            'tarballs_location': self.config.service_defaults.destination,
            'properties_location': self.config.service_defaults.properties_location,
            'remote_user': self.config.user,
        })

        stage = {
            'name': '',
            'concurrency': 1,
            'tasks': tasks,
        }

        tasklist =  {
            'name': 'Copy deployables',
            'stages': [stage],
        }

        return tasklist

