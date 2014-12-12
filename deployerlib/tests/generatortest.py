#! /usr/bin/env python

import sys
import unittest

import deployerlib.generators

from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.generator import Generator
from deployerlib.generators import *
from deployerlib.executor import Executor
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

    def verifyTasklist(self, generator):
        """Shared method to verify a generator object's task list"""
        self.log.info('Verifying task list for {0}'.format(generator.__class__.__name__))

        # Verify the generator is inheriting the Generator class
        self.assertIsInstance(generator, Generator)

        # Verify the generator returns a task list in dict form
        tasklist = generator.generate()
        self.assertIsInstance(tasklist, dict)

        # Verify that Executor is able to parse the task list
        executor = Executor(tasklist=tasklist)

    def testAllAreTested(self):
        self.log.info('Making sure there is a test for every generator')

        prefix = 'testGenerator_'
        methods = [x[len(prefix):] for x in dir(self) if x.startswith(prefix)]

        missing = set(deployerlib.generators.__all__) - set(methods)

        if missing:
            self.fail('Missing generator tests: {0}'.format(', '.join(missing)))

    def testGenerator(self):
        self.log.info('Testing Generator parent class')

        generator = Generator(self.config)
        tasklist = generator.generate()
        self.assertIsInstance(tasklist, dict)

    def testGenerator_icas(self):
        self.log.info('Testing iCAS generator')

        self.config.deployment_order = {
          'backend': [['be001', 'be002']],
          'frontend': [['fe001', 'fe002']],
        }

        generator = icas.IcasGenerator(self.config)
        self.verifyTasklist(generator)

    def testGenerator_aurora(self):
        self.log.info('Testing Aurora generator')

        self.config.platform = 'aurora'
        self.config.deployment_order = ['be-backend', 'fe-frontend']

        generator = aurora.AuroraGenerator(self.config)
        self.verifyTasklist(generator)

    @unittest.skip('Skipping ServiceControl test')
    def testGenerator_servicecontrol(self):
        self.log.info('Testing ServiceControl generator')
        # This class is not yet implemented
        pass

    def testGenerator_testgenerator(self):
        self.log.info('Testing TestGenerator')

        generator = testgenerator.TestGenerator(self.config)
        self.verifyTasklist(generator)


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
