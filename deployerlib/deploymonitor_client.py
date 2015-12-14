from deployerlib.log import Log
import requests
import time


class DeployMonitorClient:
    def __init__(self, deploy_monitor_url):
        self.deploy_monitor_url = deploy_monitor_url
        self.log = Log(self.__class__.__name__)
        self.deploy_monitor_api_url = "%s/api" % deploy_monitor_url


    def get_all_services_for_deliverable(self, deliverable):
        response = self.get_json('deliverables/%s' % deliverable)
        filtered = filter( lambda p: p['hasMain']== True, response['projects'] )
        return map(lambda p: str(p['name']), filtered)


    def get_json(self, resource, tries = 20):
        url = "%s/%s" % (self.deploy_monitor_api_url, resource)
        self.log.info("Calling GET %s" % url)

        while tries:
            tries -= 1
            try:
                r = self.request_get(url)
                if r.status_code < 300:
                    return r.json()
                else:
                    self.log.warning("Got %d status code" % r.status_code)
            except requests.ConnectionError as e:
                self.log.error(str(e))
            self.log.warning("Call resolved in error. Waiting 5 seconds. %d attempts left" % tries)
            self.sleep(5)

        raise RuntimeError("Couldn't get data from deployment monitor after %s" % tries)


    def sleep(self, seconds):
        time.sleep(seconds)


    def request_get(self, url):
        return requests.get(url)
