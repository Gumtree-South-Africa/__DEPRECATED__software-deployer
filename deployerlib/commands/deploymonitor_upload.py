import json
import re
import os

from deployerlib.exceptions import DeployerException
from deployerlib.command import Command
from deployerlib.deploymonitor_client import DeployMonitorClient
from deployerlib.deploymonitor_client import ProjectHash


class DeploymonitorUpload(Command):
    """Upload hashes to the new pipeline, to support diffing over releases
    {
      "name":"project-hashes",
        "event":{
            "deliverable":"coreservices",
            "version":"123456789",
            "projects":[{
                  "name":"nl.marktplaats.aurora-frontend",
                  "hash":"69e518fa75de765fb2fc0947cecdac6b792a9b3b",
                  "hasMain":true
                },{
                  "name":"nl.marktplaats.aurora-transaction-service",
                  "hash":"585a2d2210b411292f5320eba5a810facf5e09d3",
                  "hasMain":true
            }]
          }
        }
    """

    def initialize(self, deploy_package_dir, package_group, package_number, url, platform, proxy=None):
        self.deploy_package_dir = deploy_package_dir
        self.package_group = package_group
        self.package_number = package_number
        self.platform = platform
        self.client = DeployMonitorClient(url, proxy)
        return True


    def execute(self):
        deliverable = self.package_group
        version = self.package_number

        projects = []

        self.log.info("Using %s as deploy_package directory" % self.deploy_package_dir)

        try:
            for fileName in os.listdir(self.deploy_package_dir):
                if re.match(".*(.tar.gz|.war)", fileName):

                    name_parts = fileName.split("_")
                    if len(name_parts) < 2:
                        raise DeployerException("invalid file name, expecting at least one _, got %s" % fileName)

                    project_name = name_parts[0]
                    last_part = name_parts[-1]
                    hash = last_part.split("-")[-2]
                    projects.append(ProjectHash(project_name, hash))

        except OSError as e:
            self.log.critical("Deployment packages directory %s not present: %s or upload failed" % (deploy_package_dir, e.strerror))
            return False

        try:
            self.client.upload_project_hashes(deliverable, version, projects)
            return True
        except Exception as e:
            self.log.critical("Could not notify deploy monitor! Exception: %s" % e.strerror)
            return False

        return True
