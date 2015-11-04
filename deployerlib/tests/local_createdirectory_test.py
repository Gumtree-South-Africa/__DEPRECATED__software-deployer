#! /usr/bin/env python

import unittest
import mock

from deployerlib.commands import *

class LocalCreateDirectoryTest(unittest.TestCase):

    @mock.patch('deployerlib.commands.localcreatedirectory.shutil')
    @mock.patch('deployerlib.commands.localcreatedirectory.os')
    def test_creates_local_directory_without_removing_existing(self, mock_os, mock_shutil):
        path = "/bogus/temp/test"

        mock_os.path.exists.return_value = False
        mock_os.makedirs.return_value = True #bogus value

        createdirectory = localcreatedirectory.LocalCreateDirectory(source = path)
        createdirectory.execute()

        mock_os.path.exists.assert_called_with(path)
        mock_os.makedirs.assert_called_with(path)

    @mock.patch('deployerlib.commands.localcreatedirectory.shutil')
    @mock.patch('deployerlib.commands.localcreatedirectory.os')
    def test_should_delete_local_dir_when_clobber(self, mock_os, mock_shutil):
        path = "/bogus/temp/test"

        mock_os.path.exists.return_value = True
        mock_shutil.rmtree.return_value = True
        mock_os.makedirs.return_value = True #bogus value

        createdirectory = localcreatedirectory.LocalCreateDirectory(source = path, clobber=True)
        createdirectory.execute()

        mock_os.path.exists.assert_called_with(path)
        mock_shutil.rmtree.assert_called_with(path)
        mock_os.makedirs.assert_called_with(path)

    @mock.patch('deployerlib.commands.localcreatedirectory.shutil')
    @mock.patch('deployerlib.commands.localcreatedirectory.os')
    def test_should_return_true_if_dir_already_exists_and_no_clobber(self, mock_os, mock_shutil):
        path = "/bogus/temp/test"

        mock_os.path.exists.return_value = False
        exception = OSError()
        exception.errno = 17
        mock_os.makedirs.side_effect = exception

        createdirectory = localcreatedirectory.LocalCreateDirectory(source = path, clobber=True)
        returnval = createdirectory.execute()

        self.assertTrue(returnval)

        mock_os.path.exists.assert_called_with(path)
        mock_os.makedirs.assert_called_with(path)

if __name__ == '__main__':
    unittest.main()
