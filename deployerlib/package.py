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

        self.log.hidebug('{0} exists and is readable'.format(path))
        return True

    def split_file_extension(self, filename):
        """Trim the extension from a filename"""

        if filename.endswith('.tar.gz'):
            packagename = os.path.splitext(os.path.splitext(filename)[0])[0]
            filetype = 'tar'
        elif filename.endswith('.war'):
            packagename = os.path.splitext(filename)[0]
            filetype = 'war'
        else:
            raise DeployerException('Unsupported file type: {0}'.format(filename))

        self.log.hidebug('Package name is {0}, file type is {1}'.format(packagename, filetype))
        return packagename, filetype

    def get_servicename_from_packagename(self, packagename):
        """Extract the service name from the package name"""

        try:
            servicename = packagename.rsplit('_', 1)[0]
        except:
            raise DeployerException('Unable to extract service name from package name: {0}'.format(
              packagename))

        self.log.tag = servicename
        self.log.hidebug('Determined service name from package {0}'.format(packagename))
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
            version = packagename.rsplit('_', 1)[-1]
        except:
            raise DeployerException('Unable to extract service version from package name: {0}'.format(
              packagename))

        self.log.debug('Package version is {0}'.format(version))
        return version

    def split_version(self, version):
        """Extract SHA and timestamp from the package version"""

        try:
            sha, timestamp = version.rsplit('-', 1)
            self.log.hidebug('SHA is {0}, timestamp is {1}'.format(sha, timestamp))
        except:
            self.log.hidebug('Unable to extract SHA and timestamp from package version: {0}'.format(
              version))
            sha, timestamp = None, None

        return sha, timestamp

    def get_install_path(self, location):
        if self.filetype == 'war':
            return os.path.join(location,self.filename)
        else:
            return os.path.join(location,self.packagename)

    def get_link_path(self, location):
        if self.filetype == 'war':
            return os.path.join(location,self.servicename + '.war')
        else:
            return os.path.join(location,self.servicename)

    def get_packagename_from_path(self, path):
        basename = os.path.basename(path)
        if self.filetype != 'tar':
            filename, ext = os.path.splitext(basename)
            if ext == '.' + self.filetype:
                return filename
            else:
                raise DeployerException('Incorrect path extension {0} for path {1} found for {2} type package'.format(
                    repr(ext),repr(path),repr(self.filetype)))
        else:
            return basename

