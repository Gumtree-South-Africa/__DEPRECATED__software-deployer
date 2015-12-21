#! /usr/bin/env python2.7

# This script is used by AURORA_acceptance_tests_are_green jenkins job
# The script is needed in order to track git hashes of all test projects per package

import sys
import argparse
import requests
from deployerlib.log import Log
from deployerlib.deploymonitor_client import ProjectHash
from deployerlib.deploymonitor_client import DeployMonitorClient


class JenkinsUpstreams:
    def __init__(self, args):
        self.jenkins_job = args.job
        self.deliverable = args.deliverable
        self.package_number = args.package
        self.client = DeployMonitorClient(args.depmon)
        self.jenkins_url = args.jenkins
        self.project_has_main = True if args.type == "main" else False

        self.log = Log(self.__class__.__name__)


    def read_json(self, url):
        self.log.info("Reading json from %s" % url)
        try:
            r = requests.get(url)
            r.raise_for_status()
            return r.json()

        except Exception as e:
            self.log.critical("Could not read url: %s" % url)
            raise e


    def fetch_github_data_for_build(self, job, build):
        data = self.read_json("%s/job/%s/%s/api/json?tree=actions[lastBuiltRevision[SHA1],remoteUrls]" % (self.jenkins_url, job, build))
        for action in data["actions"]:
            if "remoteUrls" in action and "lastBuiltRevision" in action:
                remote_urls = action["remoteUrls"][0]
                hash = action["lastBuiltRevision"]["SHA1"]

                git_lookup_path = remote_urls[remote_urls.find(":") + 1:]
                if git_lookup_path.endswith(".git"):
                    git_lookup_path = git_lookup_path[0:-4]

                name = git_lookup_path[git_lookup_path.find("/") + 1:]
                return ProjectHash(name, hash, self.project_has_main, git_lookup_path)
        return None


    def fetch_test_projects_from_jenkins(self):
        upstream_projects = self.read_json("%s/job/%s/api/json?depth=1&tree=upstreamProjects[displayName,lastBuild[number]]" % (self.jenkins_url, self.jenkins_job))

        projects = []
        project_names = []

        for upstream_project in upstream_projects["upstreamProjects"]:
            job_name = upstream_project["displayName"]
            last_build = upstream_project["lastBuild"]["number"]
            project = self.fetch_github_data_for_build(job_name, last_build)

            if project.name not in project_names:
                project_names.append(project.name)
                projects.append(project)

        return projects

    def execute(self):
        projects = self.fetch_test_projects_from_jenkins()
        self.client.upload_project_hashes(self.deliverable, self.package_number, projects)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetches upstreams jobs git projects and reports them as tests for specified deliverable in deployment monitor")
    parser.add_argument("--job", type=str, required=True, help="Name of Jenkins *_are_green job (e.g. AURORA_acceptance_tests_are_green)")
    parser.add_argument("--deliverable", type=str, required=True, help="Name of deliverable in deployment monitor (e.g. aurora-core)")
    parser.add_argument("--package", type=str, required=True, help="Package version (e.g. 20151212101123)")
    parser.add_argument("--jenkins", type=str, required=True, help="Jenkins url (e.g. http://builder.platform.qa-mp.so)")
    parser.add_argument("--depmon", type=str, required=True, help="Deployment monitor app url (e.g. http://deployment-monitor.platform.qa-mp.so)")
    parser.add_argument("--type", default="test", type=str, help="Projects type (test, main)")

    args = parser.parse_args()

    jenkins_upstreams = JenkinsUpstreams(args)
    jenkins_upstreams.execute()



