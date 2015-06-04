#! /usr/bin/env python

import sys
import unittest

from deployerlib.log import Log
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.generatorhelper import GeneratorHelper
from deployerlib.executor import Executor
from deployerlib.exceptions import DeployerException


class CommandLineTest(unittest.TestCase):

    def setUp(self):
        self.log = Log(self.__class__.__name__)
        self.argv = sys.argv[:]

    def tearDown(self):
        sys.argv = self.argv

    def testNoArgs(self):
        self.log.info('Testing without arguments')

        with self.assertRaises(SystemExit):
            commandline = CommandLine()

    def testConfig(self):
        self.log.info('Testing with --config')

        sys.argv[1:] = ['--config', '/tmp/noconfig', '--logdir', '']
        commandline = CommandLine()
        self.assertEqual(commandline.config, '/tmp/noconfig')


if __name__ == '__main__':
    unittest.main()
