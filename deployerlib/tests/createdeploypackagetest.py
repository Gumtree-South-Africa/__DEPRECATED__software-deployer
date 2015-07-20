#! /usr/bin/env python

import unittest
import mock

import deployerlib.commands

class CreateDeployPackageTest(unittest.TestCase):

    @mock.patch('deployerlib.config')
    def test_execute_happy_flow(self, mock_config):
        command = CreateDeployPackage()

        command.execute()


