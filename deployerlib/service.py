import os
import sys

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException

class Service(object):
    """Manage information about a package and the service it provides"""

    def __init__(self, filename, args=None, config=None):
        self.log = Log(self.__class__.__name__)
        self.log.info('Creating service from file: {0}'.format(filename))

        self.verify_file_access(filename)

        self.fullpath = os.path.abspath(filename)
        self.filename = os.path.basename(self.fullpath)
        self.source_location = os.path.dirname(self.fullpath)

        self.packagename, self.filetype = self.split_file_extension(self.filename)
        self.servicename = self.get_servicename_from_packagename(self.packagename)
        self.servicetype = self.get_servicetype_from_servicename(self.servicename)
        self.version = self.get_version_from_packagename(self.packagename)
        self.sha, self.timestamp = self.split_version(self.version)

        if config:
            service_config = config.get(['services'])[self.servicename]
            self.deployment_type = service_config['type']

            general = config.get(['general'])
            self.upload_location = general['destination']
            self.install_location = general['webapps']

            self.remote_filename = os.path.join(self.upload_location, self.filename)
            self.install_destination = os.path.join(self.install_location, self.packagename)

            #self.add_target_hosts(self.get_remote_hosts(args, config))
            self.hosts = self.get_remote_hosts(args, config)


    def __str__(self):
        """Show readable representation"""
        return self.servicename

    def __repr__(self):
        """Show unambiguous representation"""
        return '{0}(servicename={1}, version={2})'.format(self.__class__.__name__,
          repr(self.servicename), repr(self.version))

    def verify_file_access(self, path):
        """Make sure the file exists and is readable"""

        if not os.path.isfile(path):
            raise DeployerException('Unable to create service: {0} does not exist'.format(path))

        if not os.access(path, os.R_OK):
            raise DeployerException('Unable to create service: {0} is not readable'.format(path))

        self.log.debug('{0} exists and is readable'.format(path))
        return True

    def split_file_extension(self, filename):
        """Trim the extension from a filename"""

        if filename.endswith('.tar.gz'):
            packagename = filename.replace('.tar.gz', '')
            filetype = 'tar'
        elif filename.endswith('.war'):
            packagename = filename.replace('.war', '')
            filetype = 'war'
        else:
            raise DeployerException('Unsupported file type: {0}'.format(filename))

        self.log.debug('Package name is {0}, file type is {1}'.format(packagename, filetype))
        return packagename, filetype

    def get_servicename_from_packagename(self, packagename):
        """Extract the service name from the package name"""

        try:
            servicename = packagename.split('_', 1)[0]
        except:
            raise DeployerException('Unable to extract service name from package name: {0}'.format(
              packagename))

        self.log.debug('Service name is {0}'.format(servicename))
        return servicename

    def get_servicetype_from_servicename(self, servicename):
        """Attempt to determine the service type from the service name"""

        if servicename.endswith('-frontend'):
            self.log.debug('{0} appears to be a frontend service'.format(self.servicename))
            return 'frontend'
        elif servicename.endswith('-server'):
            self.log.debug('{0} appears to be a backend service'.format(self.servicename))
            return 'backend'
        else:
            return None

    def get_version_from_packagename(self, packagename):
        """Extract the service version string from the package name"""

        try:
            version = packagename.split('_', 1)[-1]
        except:
            raise DeployerException('Unable to extract service version from package name: {0}'.format(
              packagename))

        self.log.debug('Package version is {0}'.format(version))
        return version

    def split_version(self, version):
        """Extract SHA and timestamp from the package version"""

        try:
            sha, timestamp = version.split('-')
        except:
            raise DeployerException('Unable to extract SHA and timestamp from package version: {0}'.format(
              version))

        self.log.debug('SHA is {0}, timestamp is {1}'.format(sha, timestamp))
        return sha, timestamp

    def get_remote_hosts(self, args, config):
        """Get the list of hosts this service should be deployed to"""

        hosts = []

        if args.host:
            hosts.append(args.host)

        else:
            for datacenter in config.get(['datacenters']):
                dc_config = config.get([datacenter])
                hosts += dc_config['hosts']

        self.log.info('{0} is configured to run on: {1}'.format(self.servicename, ', '.join(hosts)))
        return hosts

    def add_target_hosts(self, *hosts):
        """Add hosts to the list of target hosts"""

        for host in hosts:
            if not host in self.hosts:
                self.log.debug('Adding target host for {0}: {1}'.format(self.servicename, host))
                self.hosts.append(host)

    def remove_target_hosts(self, *hosts):
        """Remove hosts from the list of target hosts"""

        for host in hosts:
            if host in self.hosts:
                self.log.debug('Removing target host for {0}: {1}'.format(self.servicename, host))
                self.hosts = [x for x in self.hosts if x != host]
