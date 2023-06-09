#! /usr/bin/python

import os
import sys
import unittest


def get_suite():
    loader = unittest.TestLoader()
    return loader.discover(os.path.dirname(__file__), pattern='*test.py')


def run_all():
    suite = get_suite()
    runner = unittest.TextTestRunner()
    res = runner.run(suite)
    return res.wasSuccessful()


__all__ = []

for dirent in os.listdir(os.path.dirname(__file__)):

    if dirent.endswith('.py') and not dirent.startswith('_'):
        __all__.append(dirent[:-3])


if __name__ == '__main__':
    res = run_all()

    if res:
        sys.exit(0)
    else:
        sys.exit(1)
