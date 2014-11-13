import time
import socket

from deployerlib.command import Command


class SendGraphite(Command):
    """Send a metric to a carbon relay"""

    def initialize(self, carbon_host, metric_name, metric_value='1.0', carbon_port=2003, continue_on_fail=True):
        self.carbon_port = carbon_port
        self.metric_value = metric_value
        self.continue_on_fail = continue_on_fail
        return True

    def execute(self):
        sock = socket.socket()

        try:
            sock.connect((self.carbon_host, self.carbon_port))
        except:
            msg = 'Failed to connect to carbon host {0} on port {1}'.format(
                  self.carbon_host, self.carbon_port)

            if self.continue_on_fail:
                self.log.warning(msg)
                return True
            else:
                self.log.critical(msg)
                return False

        now = time.time()
        message = '%s %s %s\n' % (self.metric_name, self.metric_value, now)
        self.log.info('Sending {0} to graphite'.format(self.metric_name))

        try:
            sock.sendall(message)
        except Exception as err:
            msg = 'Error sending metric to graphite: {0}'.format(err)

            if self.continue_on_fail:
                self.log.warning(msg)
                return True
            else:
                self.log.critical(msg)
                return False

        self.log.debug('Sending message to {0}: {1}'.format(self.carbon_host, message))

        return True
