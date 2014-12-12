#! /usr/bin/env python

import unittest

from deployerlib.log import Log
from deployerlib.package import Package
from deployerlib.tests._fakepackage import FakePackage


class PackageTest(unittest.TestCase):

    def setUp(self):
        self.log = Log(self.__class__.__name__)
        self.fakepackage = FakePackage()

    def testPackage(self):
        package = Package(self.fakepackage.fullpath)
        self.log.info('Test package: {0}'.format(repr(package)))

        self.assertEquals(package.fullpath, self.fakepackage.fullpath)
        self.assertEquals(package.sha, self.fakepackage.sha)
        self.assertEquals(package.timestamp, self.fakepackage.timestamp)
        self.assertEquals(package.version, '{0}-{1}'.format(self.fakepackage.sha, self.fakepackage.timestamp))
        self.assertEquals(package.packagename, self.fakepackage.packagename)
        self.assertIn(package.servicename, self.fakepackage.servicename)
        self.assertNotEquals(package.servicename, self.fakepackage.packagename)


if __name__ == '__main__':
    unittest.main()
