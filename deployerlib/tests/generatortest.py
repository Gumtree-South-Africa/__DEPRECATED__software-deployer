#! /usr/bin/env python

import unittest

from deployerlib.log import Log
from deployerlib.config import Config
from deployerlib.generator import Generator
from deployerlib.generators import *

from deployerlib.exceptions import DeployerException


class GeneratorTest(unittest.TestCase):

    def setUp(self):
        self.log = Log(self.__class__.__name__)
        self.config = Config()

    def testGenerator(self):
        self.log.info('Testing Generator parent class')

        generator = Generator(self.config)
        tasklist = generator.generate()
        self.assertIsInstance(tasklist, dict)

    def testIcasGenerator(self):
        self.log.info('Testing iCAS generator')

        generator = icas.IcasGenerator(self.config)
        # To do: Need to get a basic config into place in order to test generate() methods


if __name__ == '__main__':
    unittest.main()
