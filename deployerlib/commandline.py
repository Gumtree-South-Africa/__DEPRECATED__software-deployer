import logging
import argparse

from deployerlib.log import Log


class CommandLine(object):
    """Handle the command line of front-end scripts"""

    def __init__(self, parents=[], require_component=True, require_host=False):
        self.log = Log(self.__class__.__name__)

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
        parser.add_argument('--parallel', type=int, default=3, help='Number of hosts to run in parallel')

        parser.parse_args(namespace=self)

        self.log.debug('CommandLine: {0}'.format(self))

    def __str__(self):
        """String representation"""

        keys = ['{0}={1}'.format(key, repr(value)) for key, value in self.__dict__.iteritems()]

        return ', '.join(keys)

    def __repr__(self):
        """Unambiguous representation"""

        return '{0}({1})'.format(self.__class__.__name__, self.__str__())
