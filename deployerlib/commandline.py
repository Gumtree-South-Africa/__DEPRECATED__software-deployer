import logging
import argparse

from deployerlib.exceptions import DeployerException


class CommandLine(object):
    """Handle the command line of front-end scripts"""

    def __init__(self, parents=[]):
        parser = argparse.ArgumentParser(parents=parents)

        parser.add_argument('-d', '--debug', action='store_true')
        parser.add_argument('-v', '--verbose', action='store_true')

        parser.add_argument('-c', '--config')

        parser.add_argument('--component')
        parser.add_argument('--directory')

        parser.add_argument('--cluster')
        parser.add_argument('--host')

        parser.add_argument('--redeploy')

        parser.parse_args(namespace=self)
