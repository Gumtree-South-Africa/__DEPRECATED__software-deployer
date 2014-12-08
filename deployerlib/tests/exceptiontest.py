#! /usr/bin/env python

import unittest

from deployerlib.exceptions import DeployerException


class ExceptionTest(unittest.TestCase):

    def testCanRaise(self):

        with self.assertRaises(DeployerException):
            raise DeployerException


if __name__ == '__main__':
    unittest.main()
