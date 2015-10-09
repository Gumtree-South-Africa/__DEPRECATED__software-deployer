from deployerlib.generator import Generator

import os
from time import strftime

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

        fe_service_names, be_service_names = filter(lambda s: "frontend" in s, services), filter(lambda s: "frontend" not in s, services)

        #TODO. Make this into a task itself
        timestamped_destination = "%s/%s-%s" % (self.config.destination, self.config.packagegroup, strftime("%Y%m%d%H%M%S")) 
        # make dir if links are non empty
        if not os.path.exists(timestamped_destination):
            os.makedirs(timestamped_destination)

        tasks.append({
            'command': 'createdeploypackage',
            'remote_host': self.config.remote_host_be,
            'timestamped_location': timestamped_destination,
            'service_names': be_service_names,
            'packagegroup': self.config.packagegroup,
            'destination': self.config.destination,
            'tarballs_location': self.config.service_defaults.destination,
            'properties_location': self.config.service_defaults.properties_location,
            'webapps_location': self.config.service_defaults.install_location,
            'remote_user': self.config.user,
        })

        tasks.append({
            'command': 'createdeploypackage',
            'remote_host': self.config.remote_host_fe,
            'timestamped_location': timestamped_destination,
            'service_names': fe_service_names,
            'packagegroup': self.config.packagegroup,
            'destination': self.config.destination,
            'tarballs_location': self.config.service_defaults.destination,
            'properties_location': self.config.service_defaults.properties_location,
            'webapps_location': self.config.service_defaults.install_location,
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

