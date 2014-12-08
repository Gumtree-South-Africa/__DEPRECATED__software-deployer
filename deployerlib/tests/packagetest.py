#! /usr/bin/env python

import os
import time
import hashlib
import datetime
import unittest

from deployerlib.log import Log
from deployerlib.package import Package
from deployerlib.exceptions import DeployerException


class PackageTest(unittest.TestCase):

    def setUp(self):
        self.log = Log(self.__class__.__name__)
        self.timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
        self.sha = hashlib.sha1().hexdigest()
        self.filename = '/tmp/deployer-unittest-package_{0}-{1}.tar.gz'.format(self.sha, self.timestamp)

        with open(self.filename, 'w') as f:
            f.close()

    def tearDown(self):
        os.remove(self.filename)

    def testPackage(self):
        package = Package(self.filename)
        self.log.info('Test package: {0}'.format(repr(package)))
        basename = os.path.basename(self.filename)

        self.assertEquals(package.fullpath, self.filename)
        self.assertEquals(package.sha, self.sha)
        self.assertEquals(package.timestamp, self.timestamp)
        self.assertEquals(package.version, '{0}-{1}'.format(self.sha, self.timestamp))
        self.assertEquals(package.packagename, basename[:-len('.tar.gz')])
        self.assertIn(package.servicename, basename)
        self.assertNotEquals(package.servicename, basename)


if __name__ == '__main__':
    unittest.main()
