import json
import requests
import re

from deployerlib.exceptions import DeployerException
from deployerlib.command import Command
from deployerlib.deploymonitor_client import DeployMonitorClient

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

    def initialize(self, url, package_group, package_version, environment, status, proxy=None, continue_on_fail=True):
        self.environment = environment
        self.package_group = package_group
        self.package_version = package_version
        self.continue_on_fail = continue_on_fail
        self.status = status
        self.client = DeployMonitorClient(url, proxy)
        return True

    def execute(self):
        try:
            self.client.notify_deployment(self.environment, self.package_group, self.package_version, self.status)
            return True
        except Exception as e:
            msg = "Could not notify deploy monitor!, Exception: %s" % e.strerror
            if self.continue_on_fail:
                self.log.warning(msg)
                return True
            else:
                self.log.critical(msg)
                return False
