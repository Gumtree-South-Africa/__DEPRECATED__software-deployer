import json
import time
import urllib2

from deployerlib.command import Command

class ConsulServiceCheck(Command):
    """Probe a consul-registered service if its healthy"""

    def initialize(self, remote_host, servicename, want_state=0, timeout=60, notify_interval=30):
        self.service_states = { 0: 'passing', 1: 'warning', 2: 'failing' }
        self.servicename = servicename
        self.want_state = 0
        if int(want_state) >= 0 and int(want_state) <= 2:
            self.want_state = int(want_state)
        self.timeout = timeout
        self.notify_interval = notify_interval
        return True

    def execute(self):
        """Put service into maintenance mode before stopping it, to gracefully prevent
        clients from connecting to the service which goes down soon"""

        # 1) query the catalog looking for service ID for this service on remote host
        #    if it is not specified, loop
        #
        # NOTE: not forward-compatible, if there are more services matching servicename
        #       on that host, it would only return one of them. This can be modified to
        #       setup maintenance mode on all services matching servicename
        #

        last_notify = time.time()
        max_time = time.time() + self.timeout
        success = False
        url = 'http://localhost:8500/v1/health/service/{servicename}?tag=node-{shorthost}&{state}'.\
                format(servicename=self.servicename, shorthost=self.remote_host.split('.')[0],
                       state = self.service_states[self.want_state])
        self.log.debug('ConsulServiceCheck URL is: {0}'.format(url))

        while time.time() < max_time and not success:

            for response in json.load(urllib2.urlopen(url)):
                if 'Service' in response and 'ID' in response['Service']:
                    success = True

            if self.notify_interval and (time.time() - last_notify) > self.notify_interval:
                time_left = int(5 * round(max_time - time.time()) / 5)
                self.log.info('Will wait up to {0} more seconds for service to enter correct state'.format(
                  time_left))
                last_notify = time.time()

            time.sleep(1)

        msg = str(res).split('|', 1)[0].rstrip()

        if success:
            self.log.debug('Check result: {0}'.format(msg))
            self.log.info('Service is in the correct state')
            return True
        else:
            self.log.critical('Service is not in the correct state within configured timeout of {0} seconds: {1}'.format(self.timeout, msg))
            return False
