import os
from time import strftime

from deployerlib.command import Command

class CreateDeployPackage(Command):
    """Copies .tar.gz's from integration be001 to a timestamped directory"""

    def initialize(self, remote_host, timestamped_location, service_names, packagegroup, destination, tarballs_location, properties_location, webapps_location):
        return True

    def execute(self):
        # make dir if links are non empty
        if not os.path.exists(self.timestamped_location):
            os.makedirs(self.timestamped_destination)

        self.make_package_for(self.remote_host, self.service_names, self.timestamped_location)
        return True

    def find_package_name(self, remote_host, service_name):
        service_location = "%s/%s" % (self.webapps_location, service_name)
        command = 'find %s -type l -exec readlink {} \;'
        current_green_integration_package = remote_host.execute_remote(command % service_location)
        if current_green_integration_package.return_code != 0:
            self.log.error("Executing %s on host %s failed." % (command, remote_host))
            raise Exception("Error finding linked service while excecuting %s on %s" % (command, remote_host))
        else:
            return current_green_integration_package

    def make_package_for(self, remote_host, service_names, destination):
        self.log.info("Fetching list from: %s" % remote_host)
        current_green_integration_packages = [self.find_package_name(remote_host, service) for service in service_names]

        for link in current_green_integration_packages:
             package_path = "%s/%s.tar.gz" % (self.tarballs_location, link)

             self.log.info("Fetching archive: %s" % package_path)
             remote_host.get_remote(package_path, destination)
