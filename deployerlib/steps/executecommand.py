from deployerlib.log import Log


class ExecuteCommand(object):
    """Execute a remote command"""

    def __init__(self, remote_host, source):
        self.log = Log(self.__class__.__name__)
        self.remote_host = remote_host
        self.source = source

    def __repr__(self):
        return '{0}(remote_host={1}, source={2})'.format(self.__class__.__name__,
          repr(1), repr(self.source))

    def execute(self, procname=None, remote_results={}):
        """Execute the remote command"""

        self.log.info('Executing command: {0}'.format(self.source))
        res = self.remote_host.execute_remote(self.source)

        if res.failed:
            self.log.critical('Failed to execute command: {0}'.format(res))

        self.log.debug('Command output: {0}'.format(res))

        remote_results[procname] = res.succeeded
        return res.succeeded
