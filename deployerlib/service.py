import os
import sys
import logging

from deployerlib.exceptions import DeployerException

class Service(object):
    """Manage information about a package and the service it provides"""

    def __init__(self, filename, upload_location='/opt/tarballs', install_location='/opt/webapps'):
        logging.info('Creating service from file: {0}'.format(filename))

        self.verify_file_access(filename)

        self.upload_location = upload_location
        self.install_location = install_location

        self.fullpath = os.path.abspath(filename)
        self.filename = os.path.basename(self.fullpath)
        self.source_location = os.path.dirname(self.fullpath)

        self.packagename, self.filetype = self.split_file_extension(self.filename)
        self.servicename = self.get_servicename_from_packagename(self.packagename)
        self.servicetype = self.get_servicetype_from_servicename(self.servicename)
        self.version = self.get_version_from_packagename(self.packagename)
        self.sha, self.timestamp = self.split_version(self.version)

    def __str__(self):
        """Show readable representation"""
        return self.servicename

    def __repr__(self):
        """Show unambiguous representation"""
        return 'Service(servicename={0}, version={1})'.format(repr(self.servicename), repr(self.version))

    def verify_file_access(self, path):
        """Make sure the file exists and is readable"""

        if not os.path.isfile(path):
            raise DeployerException('Unable to create service: {0} does not exist'.format(path))

        if not os.access(path, os.R_OK):
            raise DeployerException('Unable to create service: {0} is not readable'.format(path))

        logging.debug('{0} exists and is readable'.format(path))
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

        logging.debug('Package name is {0}, file type is {1}'.format(packagename, filetype))
        return packagename, filetype

    def get_servicename_from_packagename(self, packagename):
        """Extract the service name from the package name"""

        try:
            servicename = packagename.split('_', 1)[0]
        except:
            raise DeployerException('Unable to extract service name from package name: {0}'.format(
              packagename))

        logging.debug('Service name is {0}'.format(servicename))
        return servicename

    def get_servicetype_from_servicename(self, servicename):
        """Attempt to determine the service type from the service name"""

        if servicename.endswith('-frontend'):
            logging.debug('{0} appears to be a frontend service'.format(self.servicename))
            return 'frontend'
        elif servicename.endswith('-server'):
            logging.debug('{0} appears to be a backend service'.format(self.servicename))
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

        logging.debug('Package version is {0}'.format(version))
        return version

    def split_version(self, version):
        """Extract SHA and timestamp from the package version"""

        try:
            sha, timestamp = version.split('-')
        except:
            raise DeployerException('Unable to extract SHA and timestamp from package version: {0}'.format(
              version))

        logging.debug('SHA is {0}, timestamp is {1}'.format(sha, timestamp))
        return sha, timestamp
