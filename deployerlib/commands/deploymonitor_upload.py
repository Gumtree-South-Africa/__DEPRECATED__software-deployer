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

    def initialize(self, deploy_package_basedir, release, url, proxy=None, continue_on_fail=True):
        self.release_version = release
        self.continue_on_fail=continue_on_fail
        self.url = url
        if proxy is None:
            self.proxy = None
        else:
            self.proxy = {"http":proxy}

        return True

    def execute(self):
        self.log.info("Calling %s on deploy monitor..." % self.url)

        split_string = re.split("(.+)-(\d{14})",self.release_version)
        if not len(split_string) == 4:
            raise DeployerException("invalid package_version %s" % self.release_version)

        deliverable = split_string[1]
        version = split_string[2]

        projects = []
        deploy_package_dir = "%s/%s" % (self.deploy_package_basedir, "aurora-%s" % self.release)

        try:
            for fileName in os.listdir(deploy_package_dir):
                if re.match(".*_(.*-){3}.*(tar.gz|.war)", fileName):
                    project_name = fileName.split("_")[0]
                    hash = fileName.split("-")[len(fileName.split("-")) - 2]
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
        except:
            msg = "Could not notify deploy monitor!"
            if self.continue_on_fail:
                self.log.warning(msg)
                return True
            else:
                self.log.critical(msg)
                return False
        return True
