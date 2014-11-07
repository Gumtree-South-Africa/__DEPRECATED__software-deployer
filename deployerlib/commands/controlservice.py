import time

from deployerlib.log import Log


class ControlService(object):
    """Stop, start and check a remote service"""

    def __init__(self, remote_host, source, check_command=None, want_state=0, timeout=60):
        self.log = Log(self.__class__.__name__)
        self.remote_host = remote_host
        self.source = source
        self.check_command = check_command
        self.want_state = want_state
        self.timeout = timeout

    def __repr__(self):
        return '{0}(remote_host={1}, source={2})'.format(self.__class__.__name__,
          repr(self.remote_host.hostname), repr(self.source))

    def check_service(self):
        """Probe a service to make sure it's in the correct state"""

        maxtime = time.time() + self.timeout
        success = False

        while time.time() < maxtime:
            time.sleep(1)
            res = self.remote_host.execute_remote(self.check_command)

            if res.return_code == self.want_state:
                success = True
                break

            time.sleep(1)

        msg = str(res).split('|', 1)[0].rstrip()

        if success:
            self.log.info('Service is in the correct state: {0}'.format(msg))
            return True
        else:
            self.log.critical('Service is not in the correct state: {0}'.format(msg))
            return False

    def execute(self, procname=None, remote_results={}):
        """Control and check the service"""

        self.log.info('Controling service: {0}'.format(self.source))
        res = self.remote_host.execute_remote(self.source, use_sudo=True)

        if not res.succeeded:
            self.log.critical('Failed to control service: {0}'.format(res))
            remote_results[procname] = False
            return False

        if self.check_command:
            res = self.check_service()
            remote_results[procname] = res
            return res
        else:
            remote_results[procname] = True
            return True