#! /usr/bin/env python

import unittest
import mock
import string

from deployerlib.commands import *

class LocalCleanUpTest(unittest.TestCase):

    @mock.patch('deployerlib.commands.localcleanup.shutil')
    @mock.patch('deployerlib.commands.localcleanup.os')
    def test_cleans_up_subdirs_keeping_last_five(self, mock_os, mock_shutil):
        directory_contents = ['aurora-user-services-20151030190949',
                              'aurora-user-services-20151020020255',
                              'aurora-user-services-20151030192920',
                              'aurora-user-services-20151101021323',
                              'aurora-user-services-20151031011256',
                              'aurora-user-services-20151021010311']

        package_to_remove = 'aurora-user-services-20151020020255'

        mock_os.listdir.return_value = directory_contents
        mock_os.path.isdir.return_value = True

        dir_name = "/bogus"
        mock_shutil.rmtree.return_value = 1

        def side_effect(*args, **kwargs):
            return "%s/%s" % (args[0], args[1])
        mock_os.path.join.side_effect = side_effect

# is this needed?
        mock_os.path.join.return_value = 1

        cleanup = localcleanup.LocalCleanUp(path=dir_name,filespec="*",keepversions=5)

        cleanup.execute()

        mock_os.listdir.assert_called_with(dir_name)
        mock_shutil.rmtree.assert_called_with('/bogus/%s' % package_to_remove)

    @mock.patch('deployerlib.commands.localcleanup.shutil')
    @mock.patch('deployerlib.commands.localcleanup.os')
    def test_does_not_remove_files_when_less_then_limit(self, mock_os, mock_shutil):
        directory_contents = ['aurora-user-services-20151030190949',
                              'aurora-user-services-20151020020255',
                              'aurora-user-services-20151031011256',
                              'aurora-user-services-20151021010311']

        mock_os.listdir.return_value = directory_contents
 
        dir_name = "/bogus"
        cleanup = localcleanup.LocalCleanUp(path=dir_name,filespec="*",keepversions=5)

        cleanup.execute()

        mock_shutil.rmtree.assert_not_called

if __name__ == '__main__':
    unittest.main()
