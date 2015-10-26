#! /usr/bin/env python

import unittest
import mock

import requests

from deployerlib.commands import *

class DeployMonitorNotifyTest(unittest.TestCase):

    @mock.patch('deployerlib.commands.deploymonitor_notify.requests.post')
    def test_creates_proper_payload_for_http_call(self, mock_postrequest):
        response = requests.Response()
        response.status_code = 201
        mock_postrequest.post.return_value = response

        url = "http://deployment-monitor.platform.qa-mp.so/"
        release_version = "aurora-core-20151020132010"
        environment = "lp"

        expected_json={
            "name":"deployment",
            "event":{
                "environment": "%s" % environment,
                "deliverable": "aurora-core",
                "version": "20151020132010",
                "status": "deploying"
            }
        }

        monitor = deploymonitor_notify.DeploymonitorNotify(url=url, release_version=release_version, environment=environment, status="deploying")

        monitor.execute()

        mock_postrequest.assert_called_with(url,json=expected_json)

if __name__ == '__main__':
    unittest.main()
