from deployerlib.command import Command
from deployerlib.exceptions import DeployerException
from deployerlib.deploymonitor_client import DeployMonitorClient

class DeploymonitorCreatePackage(Command):
    """Creates package in deployment monitor app
    """

    def initialize(self, url, package_group, package_number, proxy=None):
        self.package_group = package_group
        self.package_number = package_number
        self.client = DeployMonitorClient(url, proxy)
        return True

    def execute(self):
        self.log.info("Creating package %s for %s" % (self.package_number, self.package_group))
        try:
            self.client.create_package(self.package_group, self.package_number)
            return True
        except Exception as e:
            self.log.critical(e)
            return False
