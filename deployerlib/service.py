import os
import sys
import re
from attrdict import AttrDict

from deployerlib.log import Log
from deployerlib.remotehost import RemoteHost
from deployerlib.exceptions import DeployerException

class Service(object):
    """Manage information about a package and the service it provides"""

    def __init__(self, config, filename=None, servicename=None):
        self.log = Log(self.__class__.__name__)

        self.config = config

        if filename:
            self.log.debug('Creating package from file: {0}'.format(filename))
            self.get_attributes_from_filename(filename)
        elif servicename:
            self.log.debug('Creating service from service name: {0}'.format(servicename))
            self.servicename = servicename
        else:
            raise DeployerException('{0} must be instantiated with a filename or a service name'.format(
              self.__class__.__name__))

        if not self.servicename in self.config.service:
            raise DeployerException('No service {0} defined in platform configuration'.format(self.servicename))

        self.service_config = self.config.get_with_defaults('service', self.servicename)

        if 'service_type' in self.service_config:
            self.service_type = self.service_config.service_type

        self.deployment_type = self.service_config.control_type
        self.upload_location = self.service_config.destination
        self.install_location = self.service_config.install_location

        if hasattr(self, 'filename'):
            self.remote_filename = os.path.join(self.upload_location, self.filename)

        if hasattr(self, 'packagename'):
            self.install_destination = os.path.join(self.install_location, self.packagename)

            if hasattr(self.service_config, 'unpack_dir'):
                self.unpack_dir = self.service_config.unpack_dir

                if not self.unpack_dir.startswith('/'):
                    self.unpack_dir = os.path.join(self.install_location, self.unpack_dir)

            else:
                self.unpack_dir = self.install_location

            self.unpack_destination = os.path.join(self.unpack_dir, self.packagename)

        self.symlink = os.path.join(self.install_location, self.servicename)

        if 'control' in self.service_config:
            self.control = self.service_config.control
            self.control_commands = AttrDict()
            for action in ['stop', 'start', 'restart']:
                if action in self.control:
                    self.control_commands[action] = '{0} {1} {2}/{3}'.format(
                                self.control.handler,
                                self.control[action],
                                self.service_config.location,
                                self.servicename)
            if 'check' in self.service_config:
                c = self.service_config.check
                to_replace = set(re.findall('\{[^\}]+\}',c))
                for p in to_replace:
                    v = str(eval('self.service_config.' + re.sub('[{}]','',p)))
                    c = re.sub(re.escape(p),v,c)
                self.control_commands['check'] = c

        if 'lb_service' in self.service_config:
            self.lb_service = self.service_config.lb_service

        self.hosts = self.get_remote_hosts()

    def __str__(self):

        return self.servicename

    def __repr__(self):

        return '{0}(servicename={1}, version={2})'.format(self.__class__.__name__,
          repr(self.servicename), repr(self.version))

    def get_attributes_from_filename(self, filename):
        """Gather information about a package from its filename"""

        self.verify_file_access(filename)

        self.fullpath = os.path.abspath(filename)
        self.filename = os.path.basename(self.fullpath)
        self.source_location = os.path.dirname(self.fullpath)

        self.packagename, self.filetype = self.split_file_extension(self.filename)
        self.servicename = self.get_servicename_from_packagename(self.packagename)
        self.servicetype = self.get_servicetype_from_servicename(self.servicename)
        self.version = self.get_version_from_packagename(self.packagename)
        #self.sha, self.timestamp = self.split_version(self.version)

    def verify_file_access(self, path):
        """Make sure the file exists and is readable"""

        if not os.path.isfile(path):
            raise DeployerException('Unable to create service: {0} does not exist or is not a regular file'.format(path))

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
            self.log.debug('SHA is {0}, timestamp is {1}'.format(sha, timestamp))
        except:
            self.log.debug('Unable to extract SHA and timestamp from package version: {0}'.format(
              version))
            sha, timestamp = None, None

        return sha, timestamp

    def get_remote_hosts(self):
        """Get the list of hosts this service should be deployed to"""

        if self.config.host:

            hosts = self.config.host

        else:
            hosts = []

            if 'hostgroups' in self.service_config:
                for hg in self.service_config.hostgroups:
                    hosts += self.config.hostgroup[hg]['hosts']

        if hosts:
            self.log.info('{0} is configured to run on: {1}'.format(self.servicename, ', '.join(hosts)))
        else:
            self.log.error('Cannot find any hosts to run {0} on'.format(self.servicename))

        return [RemoteHost(x, self.config.user) for x in hosts]
