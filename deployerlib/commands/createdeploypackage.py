import os
from time import strftime

from deployerlib.command import Command

class CreateDeployPackage(Command):
    """Copies .tar.gz's from integration be001 to a timestamped directory"""

    def initialize(self, remote_host_be, remote_host_fe, service_names, packagegroup, destination, tarballs_location, properties_location, webapps_location, remote_user):
        return True

    def execute(self):

        timestamped_destination = "%s/%s-%s" % (self.destination, self.packagegroup, strftime("%Y%m%d%H%M%S"))
        # make dir if links are non empty
        if not os.path.exists(timestamped_destination) and current_green_integration_packages:
            os.makedirs(timestamped_destination)

        fe_service_names, be_service_names = spit_service_into_fe_be(self.services)

        make_package_for(self.remote_host_fe, fe_service_names, timestamped_destination)
        make_package_for(self.remote_host_be, be_service_names, timestamped_destination)

        # properties, we copy it for now because not everything is puppetized
        properties_version = self.remote_host.execute_remote('cat %s/properties_version' % self.properties_location)
        if not properties_version:
            self.log.warning("Can not find installed properties version!")
            return False
        else:
            prop_file_name = "%s/%s_%s.tar.gz" % (self.tarballs_location, "*properties", properties_version)
            self.log.info("Fetching properties from %s" % prop_file_name)
            self.remote_host_be.get_remote(prop_file_name, timestamped_destination)
            return True

    def split_service_into_fe_be(self, services):
        filter(lambda s: s.contains("frontend"), services), filter(lambda s: not s.contains("frontend"), services)

    def find_package_name(self, remote_host, service_name):
        service_location = "%s/%s" % (self.webapps_location, service_name)
        current_green_integration_packages = remote_host.execute_remote('find %s -type l -exec readlink {} \;' % service_location)
        return current_green_integration_packages

    def make_package_for(self, remote_host, service_names):
        self.log.info("Fetching list from: %s" % remote_host)
        current_green_integration_packages = [self.find_package_name(remote_host, service) for service in service_names]

	for link in current_green_integration_packages:
		 package_path = "%s/%s.tar.gz" % (self.tarballs_location, link)

		 self.log.info("Fetching archive: %s" % package_path)
                 self.remote_host.get_remote(package_path, timestamped_destination)
