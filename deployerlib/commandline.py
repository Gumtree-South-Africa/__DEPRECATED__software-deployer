import logging
import argparse

from deployerlib.exceptions import DeployerException


class CommandLine(object):
    """Handle the command line of front-end scripts"""

    def __init__(self, parents=[], require_component=True, require_host=False):
        parser = argparse.ArgumentParser(parents=parents)

        output_group = parser.add_mutually_exclusive_group()
        output_group.add_argument('-v', '--verbose', action='store_true', help='Show more information')
        output_group.add_argument('-d', '--debug', action='store_true', help='Show a lot more information')

        parser.add_argument('-c', '--config', required=True, help='Specify a platform config file')

        component_group = parser.add_mutually_exclusive_group(required=require_component)
        component_group.add_argument('--component', help='Specify a single component to deploy')
        component_group.add_argument('--directory', help='Specify a directory of components to deploy')

        host_group = parser.add_mutually_exclusive_group(required=require_host)
        host_group.add_argument('--cluster', help='Specify a cluster of hosts to deploy to')
        host_group.add_argument('--host', help='Specify a single host to deploy to')

        parser.add_argument('--redeploy', action='store_true', help='Redeploy services even if they exist on remote hosts')

        parser.parse_args(namespace=self)
