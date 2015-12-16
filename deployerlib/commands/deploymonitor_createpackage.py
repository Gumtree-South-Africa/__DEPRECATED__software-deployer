from deployerlib.command import Command
from deployerlib.deploymonitor_client import DeployMonitorClient

class DeploymonitorCreatePackage(Command):
    """Creates package in deployment monitor app
    """

    def initialize(self, url, package_group, package_number, proxy=None, continue_on_fail=True):
        self.package_group = package_group
        self.package_number = package_number
        self.continue_on_fail = continue_on_fail
        self.client = DeployMonitorClient(url, proxy)
        return True

    def execute(self):
        self.log.info("Creating package %s for %s" % (self.package_number, self.package_group))
        try:
            self.client.create_package(self.package_group, self.package_number)
        except Exception as e:
            msg = "Couldn't create package %s for %s due to error: %s" % (self.package_number, self.package_group, e.strerror)
            if self.continue_on_fail:
                self.log.warning(msg)
                return True
            else:
                self.log.critical(msg)
                return False

        return True

