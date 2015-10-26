import json
import requests
import re

from deployerlib.exceptions import DeployerException
from deployerlib.command import Command

class DeploymonitorNotify(Command):
    """Notify (new) pipeline
        {
         "name":"deployment",
           "event":{
           "environment":"demo",
           "deliverable":"coreservices",
           "version":"123456789",
           "status":"deploying"
         }
       } 
    """

    def initialize(self, url, release_version, environment, status, proxy=None, continue_on_fail=True):
        self.url = url
        self.environment = environment
        self.release_version = release_version
        if proxy is None:
            self.proxy = None
        else:
            self.proxy = {"http":proxy}
        self.continue_on_fail = continue_on_fail
        self.status = status
        return True

    def execute(self):
        self.log.info("Calling %s on deploy monitor..." % self.url)
        split_string = re.split("(.+)-(\d{14})",self.release_version)

        if not len(split_string) == 4:
            raise DeployerException("invalid package_version %s" % self.release_version)

        deliverable = split_string[1]
        version = split_string[2]
        try:
            payload = {
             "name":"deployment",
               "event":{
                   "environment": self.environment,
                   "deliverable":"%s" % deliverable,
                   "version":"%s" % version,
                   "status":"%s" % self.status
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
