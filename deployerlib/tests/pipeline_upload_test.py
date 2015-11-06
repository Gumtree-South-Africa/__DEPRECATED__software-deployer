#! /usr/bin/env python

import unittest
import mock

from deployerlib.commands import *

class PipelineUploadTest(unittest.TestCase):

    @mock.patch('deployerlib.commands.pipeline_upload.os')
    @mock.patch('deployerlib.commands.pipeline_upload.urllib2')
    def test_creates_proper_payload_for_http_call(self, mock_urllib, mock_os):

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
        mock_os.path.join.return_value = full_path
        mock_os.listdir.return_value = filelist

        mock_request = mock.MagicMock()
        mock_request.add_header.return_value = True
        mock_urllib.Request.return_value = mock_request
        mock_urllib.urlopen.return_value = True 

        monitor = pipeline_upload.PipelineUpload(url=url, deploy_package_basedir=basedir, release=release_version)

        monitor.execute()

        mock_request.add_header.assert_called_with('Content-Type', 'application/json')
        mock_os.listdir.assert_called_with(full_path)
        mock_urllib.urlopen.assert_called_with(mock_request, '{"projects": [{"project": "nl.marktplaats.admarkt.admarktservice-server", "hash": "25a426d3fa68f5ee7f037bb77770c88764c2e251"}, {"project": "nl.marktplaats.advertisementhub.advertisementhub-server", "hash": "fa391e38ded8b94fbe09fe571bffe6a410b53be9"}]}')

if __name__ == '__main__':
    unittest.main()
