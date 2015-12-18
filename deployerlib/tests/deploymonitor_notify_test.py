#! /usr/bin/env python

import unittest
import mock

from deployerlib.commands import *
from deployerlib.deploymonitor_client import DeployMonitorClient


class DeployMonitorNotifyTest(unittest.TestCase):

    @mock.patch('deployerlib.deploymonitor_client.DeployMonitorClient.notify_deployment')
    def test_creates_proper_payload_for_http_call(self, mock_notify_deployment):
        monitor = deploymonitor_notify.DeploymonitorNotify(
                url="http://localhost",
                package_group="aurora-core",
                package_version="20151020132010",
                environment="lp",
                status="deploying"
            )
        monitor.execute()

        mock_notify_deployment.assert_called_with("lp", "aurora-core", "20151020132010", "deploying")

if __name__ == '__main__':
    unittest.main()
