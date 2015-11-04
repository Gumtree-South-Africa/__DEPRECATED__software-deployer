#! /usr/bin/env python

import unittest
import mock

import deployerlib.commands

class CreateDeployPackageTest(unittest.TestCase):

    @mock.patch('deployerlib.commands.createdeploypackage.os')
    @mock.patch('deployerlib.commands.createdeploypackage.remote_host')
    def test_execute_happy_flow(self, mock_remote_host, mock_os):
        command = CreateDeployPackage()

        command.execute()
