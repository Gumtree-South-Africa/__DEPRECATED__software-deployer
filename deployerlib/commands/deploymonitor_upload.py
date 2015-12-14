import json
import re
import os
import requests

from deployerlib.exceptions import DeployerException
from deployerlib.command import Command

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

    def initialize(self, deploy_package_dir, package_group, package_number, url, platform, proxy=None, continue_on_fail=True):
        self.deploy_package_dir = deploy_package_dir
        self.package_group = package_group
        self.package_number = package_number
        self.continue_on_fail = continue_on_fail
        self.url = "%s/%s" % (url, 'api/events')
        self.platform = platform

        if proxy is None:
            self.proxy = None
        else:
            self.proxy = {"http":proxy}

        return True

    def execute(self):
        self.log.info("Calling %s on deploy monitor..." % self.url)

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
                    projects.append({
                      'name':'%s' % project_name,
                      'hash':'%s' % hash,
                    })

        except OSError as e:
            msg = "Deployment packages directory %s not present: %s or upload failed" % (deploy_package_dir, e.strerror)
            if self.continue_on_fail:
                self.log.warning(msg)
                return True
            else:
                self.log.critical(msg)
                return False

        try:
            payload = {
              'name':'project-hashes',
              'event':{
                  'deliverable':'%s' % deliverable,
                  'version':'%s' % version,
                  'projects': projects
              }
            }

            self.log.info("calling: requests.post(%s, json=%s, proxies=%s)" % (self.url, payload, self.proxy))

            if self.proxy is None:
                r = requests.post(self.url, json=payload)
            else:
                r = requests.post(self.url, json=payload, proxies=self.proxy)

            r.raise_for_status()

            return True
        except Exception as e:
            msg = "Could not notify deploy monitor! Exception: %s" % e.strerror
            if self.continue_on_fail:
                self.log.warning(msg)
                return True
            else:
                self.log.critical(msg)
                return False
        return True
