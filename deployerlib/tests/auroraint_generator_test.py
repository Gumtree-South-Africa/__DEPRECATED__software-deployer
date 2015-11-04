#! /usr/bin/env python

import unittest
import mock
import collections

from deployerlib.log import Log
from deployerlib.commandline import CommandLine
import deployerlib.generators
from deployerlib.generators import *
from deployerlib.config import Config

from deployerlib.tests._fakepackage import FakePackage

class AuroraIntGeneratorTest(unittest.TestCase):

    def setUp(self):
        self.log = Log(self.__class__.__name__)

    def getConfig(self):
        return {
          'hostgroup':
          {
            'frontend': {
              'hosts': ['fe001', 'fe002'],
              'lb': 'felb001.local',
            },
            'backend': {
              'hosts': ['be001', 'be002'],
              'lb': 'felb001.local',
            },
          },
          'lb_defaults': {
            'api_user': 'nsroot',
            'api_password': 'nsroot',
          },
          'service':
          {
            'fe-frontend':
            {
              'port': 8080,
              'hostgroups': ['frontend'],
              'min_nodes_up' : 1,
            },
            'be-backend':
            {
              'port': 9090,
              'hostgroups': ['backend'],
              'min_nodes_up' : 1,
            },
          },
          'service_defaults':
          {
            'destination': '/opt/tarballs',
            'control_type': 'daemontools',
            'install_location': '/opt/webapps',
            'unpack_dir': '_unpack',
            'enabled_on_hosts': 'all',
            'check_command': '/usr/local/bin/check_service_health.py localhost {port} frontend',
            'lb_service': 'aurora_{shortservicename}_{shorthostname}.{platform}',
            'properties_location': '/tmp',
          },
          'deployment_order': ['be-backend','fe-frontend'],
          'deploy_concurrency': 1,
          'deploy_concurrency_per_host': 1,
          'non_deploy_concurrency': 1,
          'non_deploy_concurrency_per_host': 1,
          'keep_versions': 5,
          'user': 'mpdeploy',
          'environment': "demo",
          # Command line options added by the top-level deploy script
          'component': [],
          'release': [],
          'deploygroups': { 'user': ['nl.marktplaats.user.userservice-server', 'nl.marktplaats.user.shared-userservice-server']}
        }


    def test_auroraIntGeneratorShouldGenerateDirectory(self):

        commandline = CommandLine(require_config=False)
        config = Config(commandline)
        config.service = self.getConfig()['service']
        config.component = self.getConfig()['component']
        config.hostgroup = self.getConfig()['hostgroup']
        config.user = self.getConfig()['user']
        config.service_defaults = self.getConfig()['service_defaults']
        config.non_deploy_concurrency = self.getConfig()['non_deploy_concurrency']
        config.deploy_concurrency = self.getConfig()['deploy_concurrency']
        config.non_deploy_concurrency_per_host = self.getConfig()['non_deploy_concurrency_per_host']
        config.deploy_concurrency_per_host = self.getConfig()['deploy_concurrency_per_host']
        config.deployment_order = self.getConfig()['deployment_order']
        config.keep_versions = self.getConfig()['keep_versions']
        config.lb_defaults = self.getConfig()['lb_defaults']
        config.deploygroups = self.getConfig()['deploygroups']
        config.packagegroup = 'user'
        config.destination = '/tmp'
        config.remote_host_fe = 'somehost'
        config.remote_host_be = 'somehost'

        config.environment = "demo"
        config.pipeline_url = 'http://localhost:9000'
        config.deploy_monitor_url = 'http://localhost:9010'
        config.release = ['aurora-aurora-core-2015102002134000']
        config.platform = 'aurora'

        config.log = Log('TestConfig')

        # Create fake packages
        fakepackages = []

        for servicename in config.service:
            fakepackage = FakePackage(servicename=servicename)
            self.log.info('Using fake package {0}'.format(fakepackage))
            fakepackages.append(fakepackage)
            config.component.append(fakepackage.fullpath)

        generator = auroraint.AuroraIntGenerator(config)
        tasklist = generator.generate()
        self.log.info("%s" % tasklist)

    def flatten(self, l):
        for el in l:
            if isinstance(el, collections.Sequence) and not isinstance(el, basestring):
                for sub in self.flatten(el):
                    yield sub
            else:
                yield el

if __name__ == '__main__':
    unittest.main()
