import os
import sys

from deployerlib.log import Log
from deployerlib.generator import Generator
from deployerlib.exceptions import DeployerException


class IcasGenerator(Generator):
    """iCAS task list generator"""

    def generate(self):
        """Build the task list"""

        self.use_tasklist()
        packages = self.get_packages()

        if not self.config.redeploy:
            self.use_remote_versions(packages)

        # Separate active cfp hosts to reduce the number of cfp failovers during deployment
        cfp_stage = None
        for cfp_package in [x for x in packages if x.servicename.endswith('cas-cfp-service')]:
            cfp_hosts = self.config.get_service_hosts(cfp_package.servicename)
            active_cfp_host = self.get_active_cfp(cfp_package.servicename, cfp_hosts)

            if not active_cfp_host:
                continue

            self.log.info('Active {0} server: {1}'.format(cfp_package.servicename, active_cfp_host))
            cfp_stage = 'Deploy active CFP services'
            self.deploy_stage(cfp_stage, [cfp_package], only_hosts=[active_cfp_host])

        properties_packages = [x for x in packages if x.servicename.endswith('cas-properties')]
        ecg_packages = [x for x in packages if x.servicename.startswith('ecg-') and not x in properties_packages]
        tenant_packages = [x for x in packages if not x in properties_packages and not x in ecg_packages]

        if self.config.get('graphite'):
            self.graphite_stage('start')

        self.properties_stage(properties_packages)
        self.daemontools_stage(ecg_packages + tenant_packages)
        self.deploy_stage('Deploy ECG packages', ecg_packages)

        # Mark the most recently created stage
        stage_name = None

        # Deploy backend services
        for hostlist in self.config.deployment_order['backend']:
            stage_name = 'Deploy to {0}'.format(', '.join(hostlist))
            self.deploy_stage(stage_name, tenant_packages, only_hosts=hostlist)

        # Move deployment of active CFP services after other backend services
        if cfp_stage:
            self.tasklist.set_position(cfp_stage, len(self.tasklist.stages()))

        # Deploy frontend services
        for hostlist in self.config.deployment_order['frontend']:
            stage_name = 'Deploy to {0}'.format(', '.join(hostlist))
            self.deploy_stage(stage_name, tenant_packages, only_hosts=hostlist)

        # Packages which may have database migrations
        dbmig_packages = [x for x in packages if not x in properties_packages]

        # Run dbmigrations with the properties_path from the tenant-specific properties package
        for prefix in ['ecg-', 'dba-', 'kjca-', '']:
            this_packages = [x for x in dbmig_packages if x.servicename.startswith(prefix)]
            dbmig_packages = [x for x in dbmig_packages if not x in this_packages]
            properties_package = '{0}cas-properties'.format(prefix)
            self.log.debug('Using properties_path from {0} for prefix {1}'.format(properties_package, prefix))
            properties_config = self.config.get_with_defaults('service', properties_package)

            if not properties_config:
                self.log.warning('No properties package found for prefix {0}, skipping this tenant'.format(prefix))
                continue

            self.dbmigrations_stage(this_packages, properties_config.properties_path, migration_path_suffix='db')

        if self.config.get('graphite'):
            self.graphite_stage('end')

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
