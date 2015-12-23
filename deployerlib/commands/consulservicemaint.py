import json
import time
import urllib2

from deployerlib.command import Command

class ConsulServiceMaint(Command):
    """Puts a consul-registered service into maintenance mode"""

    def initialize(self, remote_host, servicename, service_id=None, delay=0):
        self.servicename = servicename
        self.service_id = service_id
        self.delay = delay
        return True

    def execute(self):
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

        if not self.service_id:
            url = 'http://localhost:8500/v1/health/service/{servicename}?tag=node-{shorthost}&passing'.\
                    format(servicename=self.servicename, shorthost=self.remote_host.split('.')[0])
            for response in json.load(urllib2.urlopen(url)):
                if 'Service' in response and 'ID' in response['Service']:
                    self.service_id = str(response['Service']['ID'])
        if not self.service_id:
            return True

        # this has to be run on the host itself - /v1/agent/service only maintains local services
        url = 'http://localhost:8500/v1/agent/service/maintenance/{service_id}?enable=true'.\
                format(service_id=self.service_id)
        cmd = 'curl -XPUT -sv \'{url}\' 2>&1 | grep -q \'^HTTP/... 200 OK$\''.format(url=url)
        res = self.remote_host.execute_remote(cmd)
        if res.return_code == 0:
            self.log.info('Service now is in the maintenance state')
            time.sleep(self.delay)
            return True
        else:
            self.log.critical('Failed to put service {0} into maintenance state: {1}'.format(self.service_id, str(res)))
            return False
