#! /usr/bin/env python

import unittest
import mock
import collections
import copy

from deployerlib.log import Log
from deployerlib.commandline import CommandLine

import deployerlib.generators
from deployerlib.generators import *
from deployerlib.config import Config

from deployerlib.tests._fakepackage import FakePackage
from deployerlib.deploymonitor_client import DeployMonitorClient


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


    @mock.patch('deployerlib.deploymonitor_client.DeployMonitorClient.get_all_services_for_deliverable')
    def test_auroraIntGeneratorShouldGenerateDirectory(self, mock_get_all_services_for_deliverable):
        mock_get_all_services_for_deliverable.return_value = [
            'nl.marktplaats.authorization.authorizationservice-server',
            'nl.marktplaats.statistics.statisticsservice-server',
            'nl.marktplaats.aurora-metrics-frontend',
            'nl.marktplaats.aurora-carsl1-frontend'
        ]

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
        generator.deploy_monitor_client = DeployMonitorClient("http://localhost")

        tasklist = generator.generate()
        self.log.info("%s" % tasklist)
        simpliefied_tasklist = self.json_simplify(tasklist, [
            'source', 'timestamped_location'
        ])

        self.assertEquals(simpliefied_tasklist, {
              'stages': [{
                  'tasks': [{
                      'source': None,
                      'command': 'local_createdirectory',
                      'clobber': False
                    },{
                      'tarballs_location': '/opt/tarballs',
                      'service_names': [
                        'nl.marktplaats.authorization.authorizationservice-server',
                        'nl.marktplaats.statistics.statisticsservice-server'
                      ],
                      'remote_user': 'mpdeploy',
                      'command': 'createdeploypackage',
                      'timestamped_location': None,
                      'webapps_location': '/opt/webapps',
                      'properties_location': '/tmp',
                      'destination': '/tmp',
                      'remote_host': 'somehost',
                      'packagegroup': 'user'
                    },{
                      'tarballs_location': '/opt/tarballs',
                      'service_names': [
                        'nl.marktplaats.aurora-metrics-frontend',
                        'nl.marktplaats.aurora-carsl1-frontend'
                      ],
                      'remote_user': 'mpdeploy',
                      'command': 'createdeploypackage',
                      'timestamped_location': None,
                      'webapps_location': '/opt/webapps',
                      'properties_location': '/tmp',
                      'destination': '/tmp',
                      'remote_host': 'somehost',
                      'packagegroup': 'user'
                    },{
                      'path': '/tmp/aurora/user',
                      'filespec': '*',
                      'command': 'local_cleanup',
                      'keepversions': 5
                    }
                  ],
                  'name': '',
                  'concurrency': 1
                }
              ],
              'name': 'Copy deployables'
            })



    def json_simplify(self, json_object, properties_for_truncation):
        copied = copy.deepcopy(json_object)
        self._simplify(copied, properties_for_truncation)
        return copied
            

    def _simplify(self, json_object, properties_for_truncation):
        if isinstance(json_object, dict):
            for key, value in json_object.iteritems():
                if key in properties_for_truncation:
                    json_object[key] = None
                else:
                    self._simplify(json_object[key], properties_for_truncation)
        elif isinstance(json_object, list):
            for value in json_object:
                self._simplify(value, properties_for_truncation)



if __name__ == '__main__':
    unittest.main()
