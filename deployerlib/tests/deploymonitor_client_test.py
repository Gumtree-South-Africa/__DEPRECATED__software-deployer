#! /usr/bin/env python

import unittest
import mock
from mock import call
from requests import ConnectionError

from deployerlib.log import Log
from deployerlib.deploymonitor_client import DeployMonitorClient


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


if __name__ == '__main__':
    unittest.main()
