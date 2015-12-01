import sys

from fabric.colors import green

from deployerlib.generators import *

from deployerlib.log import Log
from deployerlib.executor import Executor

from deployerlib.exceptions import DeployerException

class GeneratorHelper(object):
    """GeneratorHelper builder"""

    def __init__(self, config, generator_name):
        self.log = Log(self.__class__.__name__)

        generators = {
            'icas': icas.IcasGenerator,
            'aurora': aurora.AuroraGenerator,
            'supermario': aurora.AuroraGenerator,
            'aanbieding': aanbieding.AanbiedingGenerator,
            'rbb': rbb.RbbGenerator,
            'rts2': rts2.RTS2Generator,
            'csbizapp': csbizapp.CsbizappGenerator,
            'test': testgenerator.TestGenerator,
        }

        generator = generators.get(generator_name)

        if not generator:
            raise DeployerException('No callable matrix defined for platform {0}'.format(generator_name))

        self.log.debug('Using generator: {0}'.format(generator.__name__))

        self.generator_obj = generator(config)
        self.log.debug('Calling generator: {0}'.format(self.generator_obj.__class__.__name__))
        self.tasklist = self.generator_obj.generate()

    def verify_tasklist(self, ok_if_empty=True):
        """Build and return the tasklist"""

        if not self.tasklist:
            self.log.warning('Task list is empty')
            return ok_if_empty

        self.log.info('Verifying task list syntax')

        try:
            executor = Executor(tasklist=self.tasklist)
        except DeployerException as e:
            self.log.critical('Syntax is not ok: {0}'.format(e))
            return False

        del executor
        self.log.info(green('Syntax is ok'))

        return True
