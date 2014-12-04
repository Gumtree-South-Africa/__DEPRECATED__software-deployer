from deployerlib.command import Command


class TestCommand(Command):

    def initialize(self, message, optional_argument=None):
        """Initialize the test command"""

        # Note that all arguments passed to Command will be added as attributes
        # to the object. However if initialize() accepts optional arguments,
        # those must be set manually in order to retain the defaults.
        self.optional_argument = optional_argument

        self.log.info('Initializing test command: {0} / {1}'.format(
          message, optional_argument))

        return True

    def execute(self):
        self.log.info('Executing test command: {0} / {1}'.format(
          self.message, self.optional_argument))

        return True
