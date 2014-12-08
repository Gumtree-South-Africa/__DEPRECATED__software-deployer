import time

from deployerlib.command import Command

class CheckService(Command):
    """Probe a service to make sure it's in the correct state"""

    def initialize(self, remote_host, check_command, want_state=0, timeout=60, notify_interval=30):
        self.want_state = want_state
        self.timeout = timeout
        self.notify_interval = notify_interval
        return True

    def execute(self):
        """Probe a service to make sure it's in the correct state"""

        last_notify = time.time()
        max_time = time.time() + self.timeout
        success = False

        while time.time() < max_time:
            res = self.remote_host.execute_remote(self.check_command)

            if res.return_code == self.want_state:
                success = True
                break

            if self.notify_interval and (time.time() - last_notify) > self.notify_interval:
                self.log.info('Waiting for service to enter correct state')
                last_notify = time.time()

            time.sleep(1)

        msg = str(res).split('|', 1)[0].rstrip()

        if success:
            self.log.info('Service is in the correct state: {0}'.format(msg))
            return True
        else:
            self.log.critical('Service is not in the correct state: {0}'.format(msg))
            return False
