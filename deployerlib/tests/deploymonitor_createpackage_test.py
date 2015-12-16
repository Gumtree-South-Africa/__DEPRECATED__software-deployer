#! /usr/bin/env python

import unittest
import mock

import requests

from deployerlib.commands import *
from deployerlib.deploymonitor_client import DeployMonitorClient

class DeployMonitorNotifyTest(unittest.TestCase):

    @mock.patch('deployerlib.deploymonitor_client.DeployMonitorClient.create_package')
    def test_creates_proper_payload_for_http_call(self, mock_create_package):
        monitor = deploymonitor_createpackage.DeploymonitorCreatePackage(url="http://localhost", package_group="aurora-core", package_number="1234567890")
        monitor.execute()

        mock_create_package.assert_called_with("aurora-core", "1234567890")

if __name__ == '__main__':
    unittest.main()

