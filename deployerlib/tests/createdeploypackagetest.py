#! /usr/bin/env python

import unittest
import mock

from deployerlib.commands import *

'''
CreateDeployPackage(timestamped_location='/opt/deploy_packages/aurora/aurora-core/aurora-aurora-core-20160218083933', webapps_location='/opt/webapps', destination='/opt/deploy_packages', packagegroup='aurora-core', tarballs_location='/opt/tarballs', service_names=['nl.marktplaats.admarkt.admarktservice-server', 'nl.marktplaats.advertisementhub.advertisementhub-server', 'nl.marktplaats.advertisementlifecycle.advertisementlifecycle-server', 'nl.marktplaats.authorization.authorizationservice-server', 'nl.marktplaats.bidlifecycle.bidlifecycle-server', 'nl.marktplaats.bids.bids-server', 'nl.marktplaats.category.categoryservice-server', 'nl.marktplaats.contacttracking.contacttracking-service', 'nl.marktplaats.content.contentservice-server', 'nl.marktplaats.crmexporter.crmexporter-server', 'nl.marktplaats.csbizappadapter.csbizappadapterservice-server', 'nl.marktplaats.customermessaging.customermessaging-server', 'nl.marktplaats.datawarehousehub.datawarehousehub-server', 'nl.marktplaats.emailcenter.emailcenter-server', 'nl.marktplaats.favorites.favorites-server', 'nl.marktplaats.flagservice.flagservice-server', 'nl.marktplaats.labs.labsservice-server', 'nl.marktplaats.leadgeneration.leadgenerationservice-server', 'nl.marktplaats.location.locationservice-server', 'nl.marktplaats.marketplace.marketplace-server', 'nl.marktplaats.media.medialibrary-server', 'nl.marktplaats.order.orderservice-server', 'nl.marktplaats.payment.paymentservice-server', 'nl.marktplaats.postnl.postnl-service', 'nl.marktplaats.reviewhub.reviewhub-server', 'nl.marktplaats.shared-auth-service-server', 'nl.marktplaats.shared-cardetailsservice-server', 'nl.marktplaats.shared-kvkservice-server', 'nl.marktplaats.shared-pushnotification-server', 'nl.marktplaats.sitemap.sitemap-server', 'nl.marktplaats.statistics.statisticsservice-server', 'nl.marktplaats.transaction.transactionservice-server', 'nl.marktplaats.useractivity.useractivity-server', 'nl.marktplaats.userlifecycle.userlifecycle-server', 'nl.marktplaats.verification.shared-auth-verification-service-server', 'nl.marktplaats.webhooks.webhooks-server', 'nl.marktplaats.yieldoptimization.yieldoptimization-server'], tag=None, properties_location='/etc/marktplaats', remote_host=RemoteHost(hostname='be001.dro.aurora.integration.mp.ecg.so', username='mpdeploy')):
'''


class CreateDeployPackageTest(unittest.TestCase):
    class MockClass():
        return_code = 1

    class MockRemoteHost():
        def get_remote(self,path, destination):
            return "localhost"

        def execute_remote(self,s):
            return CreateDeployPackageTest.MockClass()

    @mock.patch('deployerlib.commands.createdeploypackage.os')
    def test_execute_sad_flow(self, mock_os):
        location = "102030"
        service_names = ['nl.marktplaats.admarkt.admarktservice-server']
        mock_os.path.exists(location).return_value(True)

        command = createdeploypackage.CreateDeployPackage(remote_host=self.MockRemoteHost(), timestamped_location=location, service_names=service_names, packagegroup="", destination="", 
                                                          tarballs_location="", properties_location="", webapps_location="webapps")
        with self.assertRaises(Exception):
            command.execute()


if __name__ == '__main__':
    unittest.main()
