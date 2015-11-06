#! /usr/bin/env python

import unittest
import mock

import requests

from deployerlib.commands import *

class DeployMonitorUploadTest(unittest.TestCase):

    @mock.patch('deployerlib.commands.deploymonitor_upload.os')
    @mock.patch('deployerlib.commands.deploymonitor_upload.requests.post')
    def test_creates_proper_payload_for_http_call(self, mock_postrequest, mock_os):
        response = requests.Response()
        response.status_code = 201
        mock_postrequest.post.return_value = response

        filelist = ['nl.marktplaats.admarkt.admarktservice-server_1418.1-SNAPSHOT-25a426d3fa68f5ee7f037bb77770c88764c2e251-20151007133204.tar.gz',
                    'nl.marktplaats.advertisementhub.advertisementhub-server_1328.2-SNAPSHOT-fa391e38ded8b94fbe09fe571bffe6a410b53be9-20151026170754.tar.gz'
                    ]

        url = "http://deployment-monitor.platform.qa-mp.so/"
        platform = 'aurora'
        deliverable = "aurora-core"
        version = "20151020132010"
        release_version = "%s-%s" % (deliverable, version)
        basedir = "bogus"

        full_path = "%s/%s/%s/%s-%s" % (basedir, platform, deliverable, platform, release_version)
        mock_os.join.return_value = full_path
        mock_os.listdir.return_value = filelist

        expected_json = {
          'name':'project-hashes',
            'event':{
                'deliverable':'%s' % deliverable,
                'version':'%s' % version,
                'projects':[{
                      'name':'nl.marktplaats.admarkt.admarktservice-server',
                      'hash':'25a426d3fa68f5ee7f037bb77770c88764c2e251',
                    },{
                      'name':'nl.marktplaats.advertisementhub.advertisementhub-server',
                      'hash':'fa391e38ded8b94fbe09fe571bffe6a410b53be9',
                }]
              }
            }

        monitor = deploymonitor_upload.DeploymonitorUpload(url=url, deploy_package_basedir=basedir, release=release_version, platform=platform)

        monitor.execute()

        mock_os.listdir.assert_called_with(full_path)
        mock_postrequest.assert_called_with(url,json=expected_json)

if __name__ == '__main__':
    unittest.main()
