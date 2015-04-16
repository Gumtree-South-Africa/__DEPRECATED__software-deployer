import sys
import logging
import argparse
import os
from time import gmtime, strftime

import deployerlib.log
from deployerlib.exceptions import DeployerException


class CommandLine(object):
    """Handle the command line of front-end scripts"""

    def __init__(self, parents=[], require_config=True, require_host=False, command_line=sys.argv):

        if type(parents) is not list:
            parents = [parents]

        parser = argparse.ArgumentParser(parents=parents, conflict_handler='resolve')

        output_group = parser.add_mutually_exclusive_group()
        output_group.add_argument('-v', '--verbose', action='store_true', help='Show a bit more information')
        output_group.add_argument('-d', '--debug', action='store_true', help='Show a lot more information')
        output_group.add_argument('-dd', '--hidebug', action='store_true', help='Show way too much information')

        parser.add_argument('--dry-run', action='store_true', help='Do a dry run without executing any tasks')
        parser.add_argument('-c', '--config', required=require_config, help='Specify a platform config file')
        parser.add_argument('--verify-config', action='store_true', help='Verify config file syntax')

        parser.add_argument('--ignore-lb', action='store_true', help='Ignore service state on loadbalancer')

        host_group = parser.add_mutually_exclusive_group(required=require_host)
        host_group.add_argument('--hosts', nargs='+', help='Specify a list of hosts to deploy to')
        host_group.add_argument('--hostgroups', nargs='+', metavar='HOSTGROUP', help='Specify one or more hostgroups to deploy to')
        host_group.add_argument('--categories', nargs='+', metavar='CATEGORY', help='Specify one or more categories to deploy to (replaces --cluster)')
        # supporting --cluster for backwards compatibility:
        host_group.add_argument('--cluster', choices=['frontend', 'backend', 'scrubber', 'properties', 'ranking'],
            help='Cluster to deploy to (deprecated, use --hosts, --hostgroups, or --categories)', dest='categories')

        parser.add_argument('--force', action='store_true', help='Force deployment to given hosts, hostgroups, categories, or cluster')
        parser.add_argument('--redeploy', action='store_true', help='Redeploy services even if they exist on remote hosts')
        parser.add_argument('--parallel', type=int, default=3, help='Number of hosts to run in parallel')

        parser.add_argument('--pipeline-start', action='store_true', help='Will inform pipeline that deployment was started')
        parser.add_argument('--pipeline-end', action='store_true', help='Will inform pipeline that deployment was ended')

        parser.add_argument('--logdir', default='/opt/log',
            help='Logging directory. Default value: "/opt/log". Log filename is generated from command and current time. Loglevel to file is always set to at least DEBUG.')

        parser.parse_args(command_line, namespace=self)

        if self.hidebug:
            deployerlib.log.set_level(logging.HIDEBUG)
        elif self.debug:
            deployerlib.log.set_level(logging.DEBUG)
        elif self.verbose:
            deployerlib.log.set_level(logging.VERBOSE)

        logfile=''
        if self.logdir:
            if os.path.exists(self.logdir):
                if os.path.isdir(self.logdir):
                    if os.access(self.logdir,os.W_OK):
                        cmd_base = os.path.splitext(os.path.basename(sys.argv[0]))[0]
                        ts = strftime("%Y%m%d_%H%M%S", gmtime())
                        logfile = os.path.join(self.logdir,'{0}_{1}.log'.format(cmd_base,ts))
                        deployerlib.log.set_logfile(logfile)
                    else:
                        raise DeployerException('Logdir path {0} is not writeable'.format(self.logdir))
                else:
                    raise DeployerException('Logdir path {0} is not a directory'.format(self.logdir))
            else:
                raise DeployerException('Logdir path {0} does not exist'.format(self.logdir))


        log = deployerlib.log.Log(self.__class__.__name__)
        log.info('Command called: {0}'.format(' '.join(sys.argv)))
        log.hidebug('CommandLine object: {0}'.format(self))

        if logfile:
            log.info('Using logfile {0}'.format(repr(logfile)))


    def __str__(self):
        """String representation"""

        keys = ['{0}={1}'.format(key, repr(value)) for key, value in self.__dict__.iteritems()]

        return ', '.join(keys)

    def __repr__(self):
        """Unambiguous representation"""

        return '{0}({1})'.format(self.__class__.__name__, self.__str__())

    def iteritems(self):
        return self.__dict__.iteritems()
