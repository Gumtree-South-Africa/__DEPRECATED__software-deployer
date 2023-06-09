#! /usr/bin/env python

import unittest

from deployerlib.log import Log
from deployerlib.config import Config
from deployerlib.generatorhelper import GeneratorHelper
from deployerlib.exceptions import DeployerException


class TasklistTest(unittest.TestCase):

    def setUp(self):
        self.log = Log(self.__class__.__name__)
        self.config = Config()

    def testBadGenerator(self):
        self.log.info('Testing with bad generator')

        with self.assertRaises(DeployerException):
            builder = GeneratorHelper(self.config, 'NO SUCH GENERATOR')

    def testTasklist(self):
        self.log.info('GeneratorHelper with TestGenerator')
        builder = GeneratorHelper(self.config, 'test')

        self.assertIsInstance(builder.tasklist, dict)

    def testVerifyTasklist(self):
        self.log.info('Verifying generated task list')
        builder = GeneratorHelper(self.config, 'test')
        self.assertTrue(builder.verify_tasklist())
        self.assertIn('stages', builder.tasklist)


if __name__ == '__main__':
    unittest.main()
