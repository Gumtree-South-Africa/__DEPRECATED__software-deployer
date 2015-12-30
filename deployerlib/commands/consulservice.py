import requests
import time

from deployerlib.command import Command
from deployerlib.exceptions import DeployerException


class ConsulService(Command):
    """Operate or monitor consul-registered services"""

    def initialize(self, remote_host, servicename, action, want_state=0, timeout=60, notify_interval=30,
            post_delay=0, maint_enable=True, maint_reason='Software_Deployer'):
        self.servicename = str(servicename)
        self.require_healthy = ( want_state in [0, 'passing'] )
        self.timeout = int(timeout)
        self.notify_interval = int(notify_interval)
        self.service_id_list = []
        self.post_delay = int(post_delay)
        self.maint_enable = bool(maint_enable)
        self.maint_reason = str(maint_reason)
        return True

    def execute(self):
        # Run the requested action
        return getattr(self, self.action)()

    def check(self):
        """Probe a consul-registered service if its healthy (want_state=0 or want_state=passing)
           or is not registered (any other want_state)"""
        last_notify = time.time()
        max_time = time.time() + self.timeout
        success = False
        url = 'http://localhost:8500/v1/health/service/{servicename}?tag=node-{shorthost}'.\
                format(servicename=self.servicename, shorthost=self.remote_host.hostname.split('.')[0])
        if self.require_healthy:
            url += '&passing'

        while time.time() < max_time and not success:

            try:
                req = requests.get(url)
                if req.status_code != 200:
                    response.raise_for_status()
            except Exception as e:
                raise DeployerException('Error connecting to consul API: {0}'.format(e))

            decoded_response = req.json()
            if not self.require_healthy and len(decoded_response) == 0:
                self.log.debug('Service {0} is absent, OK'.format(self.servicename))
                success = True
                continue

            for response in decoded_response:
                if 'Service' in response and 'ID' in response['Service']:
                    self.log.debug('Service {0} is present, OK'.format(self.servicename))
                    success = True
                    continue

            if self.notify_interval and (time.time() - last_notify) > self.notify_interval:
                time_left = int(5 * round(max_time - time.time()) / 5)
                self.log.info('Will wait up to {0} more seconds for service to enter required state'.format(
                    time_left))
                last_notify = time.time()

            time.sleep(1)

        if success:
            self.log.info('Service is in the required state')
            return True
        else:
            self.log.critical('Service is not in the required state within configured timeout of {0} seconds'.format(
                self.timeout))
            return False

    def maintenance(self):
        """Put service into maintenance mode before stopping it, to gracefully prevent
        clients from connecting to the service which goes down soon"""

        # 1) query the catalog looking for service ID for this service on remote host
        #    if it is not specified
        #
        # NOTE: not forward-compatible, if there are more services matching servicename
        #       on that host, it would only return one of them. This can be modified to
        #       setup maintenance mode on all services matching servicename
        #
        # 2) schedule maintenance mode on the service if found any

        shorthost = self.remote_host.hostname.split('.')[0]

        if self.maint_enable:
            opts = 'enable=true&reason={reason}'.format(reason=self.maint_reason)
        else:
            opts = 'enable=false'

        if len(self.service_id_list) == 0:
            url = 'http://127.0.0.1:8500/v1/health/service/{servicename}?tag=node-{shorthost}'.\
                    format(servicename=self.servicename, shorthost=shorthost)
            try:
                req = requests.get(url)
                if req.status_code != 200:
                    response.raise_for_status()
            except Exception as e:
                raise DeployerException('Error connecting to consul API: {0}'.format(e))

            for response in req.json():
                if 'Service' in response and 'ID' in response['Service']:
                    self.service_id_list.append(str(response['Service']['ID']))

            if len(self.service_id_list) == 0:
                self.log.warning('Failed to find service {servicename} on the node {shorthost}'.\
                    format(servicename=self.servicename, shorthost=shorthost))
                return True

        success = True
        for service_id in self.service_id_list:
            # this has to be run on the host itself - /v1/agent/service only maintains local services
            url = 'http://127.0.0.1:8500/v1/agent/service/maintenance/{service_id}?{opts}'.\
                    format(service_id=service_id, opts=opts)
            cmd = 'curl -XPUT -s -w \'{writeout}\' \'{url}\' 2>&1 | grep -q 200'.format(url=url, writeout='%{http_code}')
            self.log.debug('CMD: {cmd} on the node {shorthost}'.\
                format(cmd=cmd, shorthost=self.remote_host.hostname.split('.')[0]))

            res = self.remote_host.execute_remote(cmd)
            if res.return_code == 0:
                self.log.info('Service now is in the maintenance state')
                time.sleep(self.post_delay)
            else:
                self.log.critical('Failed to put service {0} into maintenance state: {1}'.format(service_id, str(res)))
                success = False

        return success

