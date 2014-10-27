import os
import sys
import re
from attrdict import AttrDict

from deployerlib.log import Log
from deployerlib.remotehost import RemoteHost
from deployerlib.exceptions import DeployerException

class Package(object):
    """Manage information about a package and the service it provides"""

    def __init__(self, filename):
        self.log = Log(self.__class__.__name__)

        self.verify_file_access(filename)

        self.fullpath = os.path.abspath(filename)
        self.filename = os.path.basename(self.fullpath)
        self.source_location = os.path.dirname(self.fullpath)

        self.packagename, self.filetype = self.split_file_extension(self.filename)
        self.servicename = self.get_servicename_from_packagename(self.packagename)
        self.servicetype = self.get_servicetype_from_servicename(self.servicename)
        self.version = self.get_version_from_packagename(self.packagename)
        self.sha, self.timestamp = self.split_version(self.version)

    def __str__(self):
        return self.packagename

    def __repr__(self):
        return '{0}(packagename={1}, servicename={2}, version={3})'.format(self.__class__.__name__,
          repr(self.packagename), repr(self.servicename), repr(self.version))

    def verify_file_access(self, path):
        """Make sure the file exists and is readable"""

        if not os.path.isfile(path):
            raise DeployerException('{0} does not exist or is not a regular file'.format(path))

        if not os.access(path, os.R_OK):
            raise DeployerException('{0} is not readable'.format(path))

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
