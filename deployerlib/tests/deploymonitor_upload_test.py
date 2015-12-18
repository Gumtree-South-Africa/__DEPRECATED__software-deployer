#! /usr/bin/env python

import unittest
import mock

from deployerlib.commands import *
from deployerlib.deploymonitor_client import DeployMonitorClient
from deployerlib.deploymonitor_client import ProjectHash

class DeployMonitorUploadTest(unittest.TestCase):

    @mock.patch('deployerlib.commands.deploymonitor_upload.os')
    @mock.patch('deployerlib.deploymonitor_client.DeployMonitorClient.upload_project_hashes')
    def test_creates_proper_payload_for_http_call(self, mock_upload_project_hashes, mock_os):

        filelist = ['nl.marktplaats.admarkt.admarktservice-server_1418.1-SNAPSHOT-25a426d3fa68f5ee7f037bb77770c88764c2e251-20151007133204.tar.gz',
                    'nl.marktplaats.advertisementhub.advertisementhub-server_1328.2-SNAPSHOT-fa391e38ded8b94fbe09fe571bffe6a410b53be9-20151026170754.tar.gz',
                    'nl.marktplaats.aurora-common-api-v3-frontend_d8457afac91b780f7dcf06d15cae0d5b9dc14513-20151119113948.tar.gz'
                    ]

        url = "http://localhost"
        platform = 'aurora'
        deliverable = "aurora-core"
        version = "20151020132010"
        release_version = "%s-%s" % (deliverable, version)
        basedir = "bogus"

        full_path = "%s/%s/%s/%s-%s" % (basedir, platform, deliverable, platform, release_version)
        mock_os.path.join.return_value = full_path
        mock_os.listdir.return_value = filelist

        monitor = deploymonitor_upload.DeploymonitorUpload(url=url, deploy_package_dir=full_path, package_group=deliverable, package_number=version, platform=platform)

        monitor.execute()

        mock_os.listdir.assert_called_with(full_path)
        mock_upload_project_hashes.assert_called_with("aurora-core", "20151020132010", [
            ProjectHash('nl.marktplaats.admarkt.admarktservice-server', '25a426d3fa68f5ee7f037bb77770c88764c2e251', True),
            ProjectHash('nl.marktplaats.advertisementhub.advertisementhub-server', 'fa391e38ded8b94fbe09fe571bffe6a410b53be9', True),
            ProjectHash('nl.marktplaats.aurora-common-api-v3-frontend', 'd8457afac91b780f7dcf06d15cae0d5b9dc14513', True)
        ])

if __name__ == '__main__':
    unittest.main()
