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

class AuroraGeneratorTest(unittest.TestCase):

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
        }

    @mock.patch('deployerlib.generators.aurora.AuroraGenerator.get_remote_versions')
    def test_auroraGeneratorShouldIncludeBothPipelineCommands(self, mock_get_remote_versions):
        mock_get_remote_versions.return_value = {}

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

        generator = aurora.AuroraGenerator(config)
        tasklist = generator.generate()
        self.assertTrue(self.containsPipelineNotifyAndDeployMonitorNotify(tasklist))

    def containsPipelineNotifyAndDeployMonitorNotify(self, tasklist):
        stages_exists = ('Pipeline notify deploying' in map(lambda i: i['name'], tasklist['stages'])
        and
        'Pipeline notify deployed' in map(lambda i: i['name'], tasklist['stages']))

        tasks = self.flatten(map(lambda i: i['tasks'], tasklist['stages']))
        commands = map(lambda i: i['command'], list(tasks))

        tasks_exist = ('deploymonitor_notify' in commands
        and
        'pipeline_notify' in commands)
        return stages_exists and tasks_exist

    def flatten(self, l):
        for el in l:
            if isinstance(el, collections.Sequence) and not isinstance(el, basestring):
                for sub in self.flatten(el):
                    yield sub
            else:
                yield el

if __name__ == '__main__':
    unittest.main()
