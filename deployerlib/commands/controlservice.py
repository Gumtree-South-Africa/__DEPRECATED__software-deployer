import time

from deployerlib.log import Log
import re


class ControlService(object):
    """Stop, start and check a remote service"""

    def __init__(self, remote_host, servicename, control_command, check_command=None, want_state=0, timeout=60, control_type='control'):
        self.log = Log('{0}:{1}'.format(self.__class__.__name__,servicename))
        self.servicename = servicename
        self.remote_host = remote_host
        self.control_command = control_command
        self.check_command = check_command
        self.want_state = want_state
        self.timeout = timeout
        self.control_type = control_type
        self.control_display = '{0}'.format(control_type).capitalize()

    def __repr__(self):
        return '{0}(remote_host={1}, servicename={2}, control_command={3}, check_command={4}, want_state={5}, timeout={6}, control_type={7})'.format(
            self.__class__.__name__, repr(self.remote_host.hostname), repr(self.servicename), repr(self.control_command),
            repr(self.check_command), repr(self.want_state), repr(self.timeout), repr(self.control_type))

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

        msg = re.sub('\|.*$','','Service status: {0}'.format(res.replace('\n',' ').replace('\r','')))

        if success:
            self.log.info(msg)
            return True
        else:
            self.log.critical(msg)
            return False

    def execute(self, procname=None, remote_results={}):
        """Control and check the service"""

        self.log.info('{0} with: {1}'.format(self.control_display,self.control_command))
        res = self.remote_host.execute_remote(self.control_command, use_sudo=True)

        if not res.succeeded:
            self.log.critical('Failed to control service: {0}'.format(res.replace('\n',' ').replace('\r','')))
            remote_results[procname] = False
            return False

        if self.check_command:
            res = self.check_service()
            remote_results[procname] = res
            return res
        else:
            remote_results[procname] = True
            return True
