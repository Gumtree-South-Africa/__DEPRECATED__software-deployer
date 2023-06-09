from deployerlib.generator import Generator

from deployerlib.deploymonitor_client import DeployMonitorClient

import os
from time import strftime
import json
import requests
import time
import sys

class AuroraIntGenerator(Generator):
    """Aurora integration list generator"""

    def __init__(self, config):
        super(AuroraIntGenerator, self).__init__(config)
        self.deploy_monitor_client = DeployMonitorClient(self.config.get('deploy_monitor_url'))

    def generate(self):
        """Build the task list"""

        tasks = []

        services = self.deploy_monitor_client.get_all_services_for_deliverable(self.config.packagegroup)

        fe_service_names, be_service_names = filter(lambda s: "frontend" in s, services), filter(lambda s: "frontend" not in s, services)

        self.log.info("FE services: %s" % fe_service_names)
        self.log.info("BE services: %s" % be_service_names)

        package_number = self.generate_package_number()

        timestamped_destination = "%s-%s-%s" % (self.config.platform, self.config.packagegroup, package_number)
        dir_path = os.path.join(self.config.destination, self.config.platform, self.config.packagegroup, timestamped_destination)

        tasks.append({
            'command': 'local_createdirectory',
            'source': dir_path,
            'clobber': False,
        })

        tasks.append({
            'command': 'createdeploypackage',
            'remote_host': self.config.remote_host_be,
            'timestamped_location': dir_path,
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
            'timestamped_location': dir_path,
            'service_names': fe_service_names,
            'packagegroup': self.config.packagegroup,
            'destination': self.config.destination,
            'tarballs_location': self.config.service_defaults.destination,
            'properties_location': self.config.service_defaults.properties_location,
            'webapps_location': self.config.service_defaults.install_location,
            'remote_user': self.config.user,
        })

        tasks.append(self.deploymonitor_createpackage_task(package_number))
        tasks.append(self.deploymonitor_upload_task(dir_path, package_number))

        root_dir = os.path.join(self.config.destination, self.config.platform, self.config.packagegroup)
        tasks.append({
            'command': 'local_cleanup',
            'path': root_dir,
            'filespec': "*",
            'keepversions': 5,
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


    def generate_package_number(self):
        return strftime("%Y%m%d%H%M%S")


    def deploymonitor_createpackage_task(self, package_number):
        """Create a package on deployment monitor app"""

        return {
            'command': 'deploymonitor_createpackage',
            'package_group': self.config.packagegroup,
            'package_number': package_number,
            'url': self.config.get('deploy_monitor_url'),
            'proxy': self.config.get('proxy'),
        }


    def deploymonitor_upload_task(self, deploy_package_dir, package_number):
        """Upload project of a deploypackage to the new pipeline"""
        
        return {
            'command': 'deploymonitor_upload',
            'deploy_package_dir': deploy_package_dir,
            'package_group': self.config.packagegroup,
            'package_number': package_number,
            'url': self.config.get('deploy_monitor_url'),
            'platform': self.config.get('platform'),
            'proxy': self.config.get('proxy'),
        }

