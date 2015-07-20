
from deployerlib.command import Command

class CreateDeployPackage(Command):
    """Copies .tar.gz's from integration be001 to a timestamped directory"""

    def initialize(self, remote_host, service_name, destination, tarballs_location, properties_location, webapps_location):
        return True

    def execute(self):
        self.log.info("Fetching list from: %s" % self.remote_host)

	service_location = "%s/%s" % (self.webapps_location, self.service_name)
	current_green_integration_packages = self.remote_host.execute_remote('find %s -type l -exec readlink {} \;' % service_location).splitlines()

	for link in current_green_integration_packages:
		 file_name = link.rsplit("/", 1)[-1]
		 package_path = "%s/%s.tar.gz" % (self.tarballs_location, file_name)

		 self.log.info("Fetching archive: %s" % package_path)
                 self.remote_host.get_remote(package_path, self.destination)

        # properties, we copy it for now because not everything is puppetized
        properties_version = self.remote_host.execute_remote('cat %s/properties_version' % self.properties_location)
        if not properties_version:
            self.log.warning("Can not find installed properties version!")
            return False
        else:
            prop_file_name = "%s/%s_%s.tar.gz" % (self.tarballs_location, "*properties", properties_version)
            self.log.info("Fetching properties from %s" % prop_file_name)
            self.remote_host.get_remote(prop_file_name, self.destination)
            return True
