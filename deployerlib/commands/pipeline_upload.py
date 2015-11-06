import os
import urllib2
import re
import json

from deployerlib.command import Command

class PipelineUpload(Command):
    """Upload projects of a deploy_package to pipeline"""

    def initialize(self, deploy_package_basedir, release, url, proxy=None, continue_on_fail=True):
        self.deploy_package_basedir = deploy_package_basedir
        self.release = release
        self.url = url
        self.proxy = proxy
        self.continue_on_fail = continue_on_fail
        return True

    def execute(self):
        self.log.info("Uploading projects of %s to pipeline..." % self.release)

        split_string = re.split("(.+)-(\d{14})",self.release)
        if not len(split_string) == 4:
            raise DeployerException("invalid package_version %s" % self.release)

        deliverable = split_string[1]
        version = split_string[2]

        projects = []
        deploy_package_dir = os.path.join(self.deploy_package_basedir, 'aurora', deliverable, '%s-%s' % ('aurora',self.release))
        self.log.info("Using %s as deploy_package directory" % deploy_package_dir)

        try:
            for fileName in os.listdir(deploy_package_dir):
                if re.match(".*_(.*-){3}.*(tar.gz|.war)", fileName):
                    suffix = fileName.split("_")[0]
                    sp = fileName.split("-")
                    projects.append({'project' : suffix, 'hash' : sp[len(sp) - 2]})

            req = urllib2.Request(self.url)
            req.add_header('Content-Type', 'application/json')
            if self.proxy:
                req.set_proxy(self.proxy, 'http')
            urllib2.urlopen(req, json.dumps({'projects' : projects}))
            return True
        except OSError as e:
            msg = "Deployment packages directory %s not present: %s or upload failed" % (deploy_package_dir, e.strerror)
            if self.continue_on_fail:
                self.log.warning(msg)
                return True
            else:
                self.log.critical(msg)
                return False

