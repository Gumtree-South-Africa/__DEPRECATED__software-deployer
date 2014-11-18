import time

from deployerlib.log import Log

from deployerlib.exceptions import DeployerException


class Command(object):
    """Framework for a remote command to be run with JobQueue"""

    def __init__(self, **kwargs):
        self.tag = kwargs.pop('tag', None)
        self.log = Log(instance=self.__class__.__name__, tag=self.tag)

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        self.log.debug('Initializing class: {0}'.format(repr(self)))
        res = self.initialize(**kwargs)

        if not res:
            raise DeployerException('Failed to initialize {0}: initialize() returned {1}'.format(
              repr(self), repr(res)))

        self.log.debug('Command initialized successfully: {0}'.format(repr(self)))

    def __repr__(self):
        attrs = ', '.join(['{0}={1}'.format(key, repr(value)) for key, value in vars(self).iteritems() if key != 'log'])
        return '{0}({1})'.format(self.__class__.__name__, attrs)

    def initialize(self, **kwargs):
        """Classes can optionally use this method to verify the input provided to their command
           or provide further initialization.
        """

        return True

    def execute(self):
        """Classes provide their functionality in this method"""

        self.log.warning('Command doing nothing: {0}'.format(repr(self)))
        return True

    def thread_execute(self, procname=None, remote_results={}):
        """Executor runs this method, which calls self.execute and returns the results"""

        start_time = time.time()

        res = self.execute()

        duration = int(time.time() - start_time)
        self.log.verbose('Task execution finished, duration {0} seconds'.format(duration))

        remote_results[procname] = res
        return res
