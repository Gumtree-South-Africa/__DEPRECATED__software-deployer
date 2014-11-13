import time

from deployerlib.command import Command

class CheckService(Command):
    """Probe a service to make sure it's in the correct state"""

    def initialize(self, remote_host, check_command, want_state=0, timeout=60):
        self.want_state = want_state
        self.timeout = timeout
        return True

    def execute(self):
        """Probe a service to make sure it's in the correct state"""

        maxtime = time.time() + self.timeout
        success = False

        while time.time() < maxtime:
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
