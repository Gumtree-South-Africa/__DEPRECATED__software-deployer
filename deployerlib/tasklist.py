import sys

from fabric.colors import green

from deployerlib.generators import *

from deployerlib.log import Log
from deployerlib.executor import Executor


class Tasklist(object):
    """Tasklist builder"""

    def __init__(self, config, generator_name):
        self.log = Log(self.__class__.__name__)

        generators = {
          'pmcconnell': pmcconnell.DemoGenerator,
          'icas': icas.IcasGenerator,
          'aurora': aurora.AuroraGenerator,
        }

        generator = generators.get(config.platform)

        if not generator:
            raise DeployerException('No callable matrix defined for platform {0}'.format(config.platform))

        self.log.debug('Using generator: {0}'.format(generator.__name__))

        self.generator_obj = generator(config)

    def build(self):
        """Build and return the tasklist"""

        self.log.debug('Calling generator: {0}'.format(self.generator_obj.__class__.__name__))

        tasklist = self.generator_obj.generate()

        if tasklist:

            self.log.info('Verifying task list syntax')

            try:
                executor = Executor(tasklist=tasklist)
            except DeployerException as e:
                self.log.critical('Syntax is not ok: {0}'.format(e))
                sys.exit(1)

            del executor
            self.log.info(green('Syntax is ok'))
        else:
            self.log.warning('Task list is empty')

        return tasklist
