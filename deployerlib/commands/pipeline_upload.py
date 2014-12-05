import os
import urllib2
import re
import json

from deployerlib.command import Command

class PipelineUpload(Command):
    """Upload projects of a deploy_package to pipeline"""

    def initialize(self, deploy_package_basedir, release, url, proxy='', continue_on_fail=True):
        self.deploy_package_basedir = deploy_package_basedir
        self.release = release
        self.url = url
        self.proxy = proxy
        self.continue_on_fail = continue_on_fail
        return True

    def execute(self):
        self.log.info("Uploading projects of %s to pipeline..." % self.release)

        projects = []
        deploy_package_dir = "%s/%s" % (self.deploy_package_basedir, self.release)

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
            print json.dumps({'projects' : projects})
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

