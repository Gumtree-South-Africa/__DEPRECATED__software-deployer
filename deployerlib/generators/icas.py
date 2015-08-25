import os
import sys

from deployerlib.log import Log
from deployerlib.generator import Generator
from deployerlib.exceptions import DeployerException


class IcasGenerator(Generator):
    """iCAS task list generator"""

    def generate(self):
        """Build the task list"""

        packages = self.get_packages()

        if not self.config.redeploy:
            self.use_remote_versions(packages)

        properties_packages = [x for x in packages if x.servicename.endswith('cas-properties')]
        packages = [x for x in packages if not x in properties_packages]

        cfp_stage = self.get_cfp_stage([x for x in packages if x.servicename.endswith('cas-cfp-service')])

        self.deploy_properties(properties_packages)
        self.daemontools_stage(packages)
        self.deploy_ordered_packages(packages, self.config.deployment_order)

        # Move Active CFP stage after inactive CFP stage
        if cfp_stage and cfp_stage in self.tasklist.stages():
            self.move_cfp_stage(cfp_stage)

        # Packages that may have dbmigrations
        dbmig_packages = packages[:]

        # Run dbmigrations with the properties_path from the tenant-specific properties package
        for prefix in ['ecg-', 'dba-', 'kjca-', '']:
            # Prune the list so the last iteration contains only non-prefixed packages
            this_packages = [x for x in dbmig_packages if x.servicename.startswith(prefix)]
            dbmig_packages = [x for x in dbmig_packages if not x in this_packages]

            # The properties package for this prefix
            properties_package = '{0}cas-properties'.format(prefix)
            self.log.debug('Using properties_path from {0} for prefix {1}'.format(properties_package, prefix))

            try:
                properties_config = self.config.get_with_defaults('service', properties_package)
            except DeployerException:
                self.log.warning('No properties package found for prefix {0}, skipping DB migrations for this tenant'.format(prefix))
                continue

            self.dbmigrations_stage(this_packages, properties_config.properties_path, migration_path_suffix='db')

        if self.config.release and not self.tasklist.is_empty():
            self.use_graphite()

        return self.tasklist.generate()

    def get_active_cfp(self, servicename, hostlist):
        """Find the active cfp server"""

        self.log.info('Determining active cfp host')

        active_host = None
        log_cmd = 'tail -n 1000 /opt/logs/{0}.log | grep "Start handling batch with" | grep -v "Start handling batch with 0 events"'.format(servicename)

        for hostname in hostlist:
            remote_host = self.get_remote_host(hostname, self.config.user)

            try:
                res = remote_host.execute_remote(log_cmd)
            except (Exception, SystemExit):
                self.log.info('Failed to connect to {0}, skipping check for active {1} host'.format(hostname, servicename))
                return
            else:
                if res.succeeded and res.return_code == 0:
                    self.log.info('{0} service is active on {1}'.format(servicename, hostname))
                    return hostname

        self.log.warning('Unable to find active host for {0}, will deploy with concurrency'.format(servicename))

    def get_cfp_stage(self, cfp_packages):
        """Separate active cfp hosts to reduce the number of cfp failovers during deployment"""

        cfp_stage = None

        for cfp_package in cfp_packages:
            cfp_hosts = self.config.get_service_hosts(cfp_package.servicename)
            active_cfp_host = self.get_active_cfp(cfp_package.servicename, cfp_hosts)

            if not active_cfp_host:
                continue

            self.log.info('Active {0} server: {1}'.format(cfp_package.servicename, active_cfp_host))
            cfp_stage = 'Deploy active CFP services'
            self.deploy_packages([cfp_package], only_hosts=[active_cfp_host], stage_name=cfp_stage)

        return cfp_stage

    def move_cfp_stage(self, cfp_stage):
        """Re-order active cfp deployment stage after inactive cfp deployment stage"""

        inactive_stage_pos = 0

        for stage in [x for x in self.tasklist.stages() if 'cas-cfp-service' in x]:
            pos = self.tasklist.get_position(stage)
            if pos > inactive_stage_pos:
                inactive_stage_pos = pos

        if not inactive_stage_pos:
            self.log.warning('Unable to find inactive CFP deployment stage, not repositioning active CFP stage')

        self.log.debug('Moving active CFP stage to tasklist position {0}'.format(inactive_stage_pos))
        self.tasklist.set_position(cfp_stage, inactive_stage_pos)
