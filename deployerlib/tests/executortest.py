#! /usr/bin/env python

import unittest

from deployerlib.log import Log
from deployerlib.config import Config
from deployerlib.generatorhelper import GeneratorHelper
from deployerlib.executor import Executor
from deployerlib.exceptions import DeployerException


class ExecutorTest(unittest.TestCase):

    def setUp(self):
        self.log = Log(self.__class__.__name__)
        self.config = Config()
        self.builder = GeneratorHelper(self.config, 'test')

    def testEmptyTasklist(self):
        self.log.info('Testing with empty task list')

        with self.assertRaises(DeployerException):
            executor = Executor(tasklist={})

    def testInstantiateExecutor(self):
        self.log.info('Testing with generated task list')
        executor = Executor(tasklist=self.builder.tasklist)

    def testRunExecutor(self):
        self.log.info('Executing generated task list')
        executor = Executor(tasklist=self.builder.tasklist)
        self.assertTrue(executor.run())


if __name__ == '__main__':
    unittest.main()
