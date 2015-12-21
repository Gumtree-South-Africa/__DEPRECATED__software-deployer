#! /usr/bin/env python

import unittest
import mock
from mock import call
from requests import ConnectionError

from deployerlib.log import Log
from deployerlib.deploymonitor_client import DeployMonitorClient
from deployerlib.deploymonitor_client import ProjectHash


class DeploymentMonitorClientTest(unittest.TestCase):

    def setUp(self):
        self.log = Log(self.__class__.__name__)

    @mock.patch('deployerlib.deploymonitor_client.DeployMonitorClient.sleep')
    @mock.patch('deployerlib.deploymonitor_client.DeployMonitorClient.request_get')
    def test_clientShouldRetryInCaseOfConnectionErrors(self, mock_request_get, mock_sleep):
        mock_request_get.side_effect = ConnectionError("500 Server error")
        client = DeployMonitorClient("http://localhost")

        with self.assertRaises(RuntimeError):
            client.get_json("/some-resource")

        mock_sleep.assert_has_calls([call(5)] * 20)


    @mock.patch('deployerlib.deploymonitor_client.DeployMonitorClient.request_post')
    def test_clientShouldCreatePackage(self, mock_request_post):
        client = DeployMonitorClient("http://localhost")
        client.create_package("aurora-core", "123456789")

        mock_request_post.assert_has_calls([
            call('http://localhost/api/events', {'name': 'package-create', 'event': {'deliverable': 'aurora-core', 'version': '123456789'}}),
            call().raise_for_status()
        ])


    @mock.patch('deployerlib.deploymonitor_client.DeployMonitorClient.request_post')
    def test_clientShouldNotifyDeployment(self, mock_request_post):
        client = DeployMonitorClient("http://localhost")
        client.notify_deployment("demo", "aurora-core", "1234567890", "deploying")

        mock_request_post.assert_has_calls([
            call('http://localhost/api/events', {
                'name': 'deployment', 
                'event': {
                    'environment': 'demo',
                    'deliverable': 'aurora-core', 
                    'version': '1234567890',
                    'status': 'deploying'
                }
            }),
            call().raise_for_status()
        ])

        client.notify_deployment("demo", "aurora-core", "1234567890", "deployed")

        mock_request_post.assert_has_calls([
            call('http://localhost/api/events', {
                'name': 'deployment', 
                'event': {
                    'environment': 'demo',
                    'deliverable': 'aurora-core', 
                    'version': '1234567890',
                    'status': 'deployed'
                }
            }),
            call().raise_for_status()
        ])


    @mock.patch('deployerlib.deploymonitor_client.DeployMonitorClient.request_post')
    def test_clientShouldUploadProjects(self, mock_request_post):
        client = DeployMonitorClient("http://localhost")
        client.upload_project_hashes("aurora-core", "1234567890", [
            ProjectHash("nl.marktplaats.aurora-frontend", "69e518"),
            ProjectHash("nl.marktplaats.aurora-transaction-service", "qweasdzc"),
            ProjectHash("selenium-tests", "123546", False, "http://example.com/some/github/lookup")
        ])

        mock_request_post.assert_has_calls([
            call('http://localhost/api/events', {
                'name': 'project-hashes', 
                'event': {
                    'deliverable': 'aurora-core', 
                    'version': '1234567890',
                    'projects': [{
                        "name": "nl.marktplaats.aurora-frontend",
                        "hash": "69e518",
                        "hasMain": True
                    },{
                        "name": "nl.marktplaats.aurora-transaction-service",
                        "hash": "qweasdzc",
                        "hasMain": True
                    },{
                        "name": "selenium-tests",
                        "hash": "123546",
                        "hasMain": False,
                        "gitLookupPath": "http://example.com/some/github/lookup"
                    }]
                }
            }),
            call().raise_for_status()
        ])

if __name__ == '__main__':
    unittest.main()
