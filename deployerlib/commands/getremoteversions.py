from deployerlib.command import Command
import os


class GetRemoteVersions(Command):

    def initialize(self, remote_host, remote_versions, install_location, properties_defs):
        """Initialize the test command"""

        return True

    def execute(self):
        # this is how we determine if we're dealing with properties or services
        if self.properties_defs:
            res = self.get_properties_versions()
            if not res:
                return False
        if self.install_location:
            res = self.get_services_versions()
            if not res:
                return False
        return True

    def get_services_versions(self):
        # instead of readlink on one service at a time per fabric connection, we're getting the whole dir of services and versions
        res = self.remote_host.execute_remote("/usr/bin/find {0} -maxdepth 1 -type l -exec /bin/readlink {{}} \\;".format(self.install_location))
        if res:
            for item in res.splitlines():
                if not item:
                    continue
                item = os.path.basename(item)
                name_vers = item.split('_')
                service_name = name_vers[0]
                remote_version = name_vers[1]
                jbname = '{0}/{1}'.format(self.remote_host.hostname, service_name)
                self.remote_versions[jbname] = remote_version
                self.log.info("{0}:{1}".format(service_name, remote_version))

        if not res.succeeded:
            self.log.debug('Failed to get remote versions: {0}'.format(res))

        return True

    def get_properties_versions(self):
        # todo: this won't work for iCas yet due to mp/dba separation and properties_location not existing yet)
        for prop_name, prop_path in self.properties_defs:
            res = self.remote_host.execute_remote("/bin/cat %s/properties_version" % prop_path)
            if res.failed:
                self.log.debug('Failed to get properties version from %s/properties_version' % prop_path)
                return True
            jbname = '{0}/{1}'.format(self.remote_host.hostname, prop_name)
            self.remote_versions[jbname] = res
            self.log.info("{0}:{1}".format(prop_name, res))
        return True
