#! /usr/bin/env python

import sys
import unittest

from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.generator import Generator
from deployerlib.generators import *
from deployerlib.tests._fakepackage import FakePackage


class GeneratorTest(unittest.TestCase):

    def setUp(self):
        self.log = Log(self.__class__.__name__)
        commandline = CommandLine(require_config=False)
        testconfig = dict(commandline.__dict__.items() + get_config().items())
        self.config = Config(testconfig)
        self.config.log = Log('TestConfig')

        # Create fake packages
        self.fakepackages = []

        for servicename in self.config.service:
            fakepackage = FakePackage(servicename=servicename)
            self.log.info('Using fake package {0}'.format(fakepackage))
            self.fakepackages.append(fakepackage)
            self.config.component.append(fakepackage.fullpath)

    def testGenerator(self):
        self.log.info('Testing Generator parent class')

        generator = Generator(self.config)
        tasklist = generator.generate()
        self.assertIsInstance(tasklist, dict)

    def testIcasGenerator(self):
        self.log.info('Testing iCAS generator')

        self.config.deployment_order = {
          'backend': [['be001', 'be002']],
          'frontend': [['fe001', 'fe002']],
        }

        generator = icas.IcasGenerator(self.config)
        tasklist = generator.generate()

    def testAuroraGenerator(self):
        self.log.info('Testing Aurora generator')

        self.config.platform = 'aurora'
        self.config.deployment_order = ['be-backend', 'fe-frontend']

        generator = aurora.AuroraGenerator(self.config)
        tasklist = generator.generate()


def get_config():

    return {
      'hostgroup':
      {
        'frontend': {
          'hosts': ['fe001', 'fe002'],
        },
        'backend': {
          'hosts': ['be001', 'be002'],
        },
      },
      'service':
      {
        'fe-frontend':
        {
          'port': 8080,
          'hostgroups': ['frontend'],
        },
        'be-backend':
        {
          'port': 9090,
          'hostgroups': ['backend'],
        },
      },
      'service_defaults':
      {
        'destination': '/opt/tarballs',
        'control_type': 'daemontools',
        'install_location': '/opt/webapps',
        'unpack_dir': '_unpack',
        'enabled_on_hosts': 'all',
      },
      'deployment_order': None,
      'deploy_concurrency': 1,
      'deploy_concurrency_per_host': 1,
      'non_deploy_concurrency': 1,
      'non_deploy_concurrency_per_host': 1,
      'keep_versions': 5,
      'user': None,
      'environment': None,
      # Command line options added by the top-level deploy script
      'component': [],
      'release': [],
    }


if __name__ == '__main__':
    unittest.main()
