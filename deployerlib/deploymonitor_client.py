from deployerlib.log import Log
import requests
import time


class ProjectHash:
    def __init__(self, name, hash, has_main=True):
        self.name = name
        self.hash = hash
        self.has_main = has_main


    def __repr__(self):
        return "ProjectHash(name=%s, hash=%s, has_main=%s)" % (self.name, self.hash, self.has_main)


    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)


    def __ne__(self, other):
        return not self.__eq__(other)


    def get_json(self):
        return {
            "name": self.name,
            "hash": self.hash,
            "hasMain": self.has_main
        }




class DeployMonitorClient:
    def __init__(self, deploy_monitor_url, proxy=None):
        self.deploy_monitor_url = deploy_monitor_url
        self.log = Log(self.__class__.__name__)
        self.deploy_monitor_api_url = "%s/api" % deploy_monitor_url
        self.proxy = proxy


    def create_package(self, deliverable, package_number):
        """ Crates a package with specified version for specified deliverable

        Keyword arguments:
        deliverable     -- the name of deliverable (e.g. "aurora-core")
        package_number  -- version of deliverable package (e.g. "20151217101023")
        """
        self.post_json("events", {
            "name": "package-create",
            "event": {
                "deliverable": deliverable,
                "version": package_number
            }
        })


    def upload_project_hashes(self, deliverable, package_number, projects):
        """ Uploads projects with hashes for specified package in specified deliverable
    
        Keyword arguments:
        deliverable     -- the name of deliverable (e.g. "aurora-core")
        package_number  -- version of deliverable package (e.g. "20151217101023")
        projects        -- list of ProjectHash objects (e.g. [ProjectHash("aurora-frontend","123qwe", True), ProjectHash("selenium-tests", "asd34324", False)])
        """

        self.post_json("events", {
            "name": "project-hashes",
            "event": {
                "deliverable": deliverable,
                "version": package_number,
                "projects": map(lambda p: p.get_json(), projects)
            }
        })


    def notify_deployment(self, environment, deliverable, package_number, status):
        """ Updates deployment status for a specified package on a specified environment

        Keyword arguments:
        environment     -- name of environment (e.g. "demo")
        deliverable     -- the name of deliverable (e.g. "aurora-core")
        package_number  -- version of deliverable package (e.g. "20151217101023")
        status          -- status of deployment ("deploying", "deployed", "crashed")
        """
        self.post_json("events", {
            'name': 'deployment', 
            'event': {
                'environment': environment,
                'deliverable': deliverable, 
                'version': package_number,
                'status': status
            }
        })


    def get_all_services_for_deliverable(self, deliverable):
        """ Returns all services/projects for specified deliverable
        This call is used by package creator in order to get all the services
        it is supposed to put in a new package

        Keyword arguments:
        deliverable     -- the name of deliverable (e.g. "aurora-core")
        """
        response = self.get_json('deliverables/%s' % deliverable)
        filtered = filter( lambda p: p['hasMain']== True, response['projects'] )
        return map(lambda p: str(p['name']), filtered)


    def post_json(self, resource, payload):
        url = "%s/%s" % (self.deploy_monitor_api_url, resource)
        self.log.info("calling: requests.post('%s', json=%s, proxies=%s)" % (url, payload, self.proxy))
        r = self.request_post(url, payload)
        r.raise_for_status()


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


    def request_post(self, url, payload):
        if self.proxy is None:
            return requests.post(url, json=payload)
        else:
            return requests.post(url, json=payload, proxies={"http":self.proxy})
