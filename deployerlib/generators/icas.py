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
            remote_versions = self.get_remote_versions(packages)

        task_list = {
          'name': 'iCAS deployment',
          'stages': [],
        }

        upload_tasks = []
        create_temp_tasks = []
        unpack_tasks = []
        dbmig_tasks = []
        properties_tasks = []
        daemontools_tasks = []
        deploy_tasks = []
        cfp_tasks = []
        remove_temp_tasks = []
        cleanup_tasks = []

        tempdir_done = []
        migration_done = []
        properties_done = []

        if [x for x in packages if x.servicename.endswith('-cfp-service')]:
            active_cfp_host = self.get_active_cfp(self.config.get_service_hosts('cas-cfp-service'))
            self.log.info('Active cfp server is {0}'.format(active_cfp_host))
        else:
            active_cfp_host = None

        for package in packages:

            if hasattr(self.config, 'ignore_packages'):

                if not hasattr(self.config.ignore_packages, '__iter__'):
                    self.config.ignore_packages = [self.config.ignore_packages]

                if package.servicename in self.config.ignore_packages:
                    self.log.info('Skipping package {0} because it is in "ignore_packages"'.format(
                      package.servicename))
                    continue

            service_config = self.config.get_with_defaults('service', package.servicename)

            if not service_config:
                raise DeployerException('Unknown service: {0}'.format(package.servicename))

            configured_hosts = self.config.get_service_hosts(package.servicename)

            if self.config.hosts:

                if set(self.config.hosts) < set(configured_hosts):
                    hosts = self.config.hosts
                else:
                    self.log.critical('Service {0} is not configured to run on host {1}'.format(
                      package.servicename, ' or '.join(self.config.hosts)))
                    sys.exit(1)

            else:
                hosts = configured_hosts

            if not hosts:
                self.log.warning('Service {0} is not configured to run on any hosts'.format(
                  package.servicename))

            for hostname in hosts:

                if not self.config.redeploy and remote_versions.get(package.servicename) and \
                  remote_versions.get(package.servicename).get(hostname) == package.version:\

                    self.log.info('Service {0} is up to date on {1}, skipping'.format(
                      package.servicename, hostname))
                    continue

                upload_tasks.append({
                  'command': 'upload',
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                  'source': package.fullpath,
                  'destination': service_config.destination,
                  'tag': package.servicename,
                })

                unpack_tasks.append({
                  'command': 'unpack',
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                  'source': os.path.join(service_config.destination, package.filename),
                  'destination': os.path.join(service_config.install_location, service_config.unpack_dir),
                  'tag': package.servicename,
                })

                # clean up upload directory
                cleanup_tasks.append({
                  'command': 'cleanup',
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                  'path': service_config.destination,
                  'filespec': '{0}_*'.format(package.servicename),
                  'keepversions': self.config.keep_versions,
                  'tag': package.servicename,
                })

                # handle unpack directories
                if not hostname in tempdir_done:
                    tempdir_done.append(hostname)

                    create_temp_tasks.append({
                      'command': 'createdirectory',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': os.path.join(service_config.install_location, service_config.unpack_dir),
                      'clobber': True,
                    })

                    remove_temp_tasks.append({
                      'command': 'removefile',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': os.path.join(service_config.install_location, service_config.unpack_dir),
                    })

                # handle database migrations
                if service_config.get('migration_command') and not package.servicename in migration_done:
                    migration_done.append(package.servicename)

                    if package.servicename.startswith('cas-') or package.servicename.startswith('shared-'):
                        properties_config = self.config.get_with_defaults('service', 'cas-properties')
                    elif package.servicename.startswith('dba-'):
                        properties_config = self.config.get_with_defaults('service', 'dba-cas-properties')
                    else:
                        raise DeployerException('Unable to determine properties path for service: {0}'.format(
                          package.servicename))

                    properties_path = properties_config.properties_path

                    unpack_location = os.path.join(service_config.install_location, service_config.unpack_dir, package.packagename)
                    dbmig_location = os.path.join(unpack_location, 'db')

                    dbmig_tasks.append({
                      'command': 'dbmigration',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': service_config.migration_command.format(
                        unpack_location=unpack_location,
                        properties_path=properties_path,
                      ),
                      'tag': package.servicename,
                      'if_exists': dbmig_location,
                    })

                # handle properties package
                if package.servicename == 'cas-properties' or package.servicename == 'dba-cas-properties':

                    if not (hostname, package.servicename) in properties_done:
                        properties_done.append((hostname, package.servicename))

                        properties_tasks.append({
                          'command': 'copyfile',
                          'remote_host': hostname,
                          'remote_user': self.config.user,
                          'source': '{0}/*'.format(os.path.join(service_config.install_location,
                          service_config.unpack_dir, package.packagename, service_config.environment)),
                          'destination': '{0}/'.format(service_config.properties_path),
                          'continue_if_exists': True,
                          'tag': package.servicename,
                        })

                    # no further work required for deploying properties
                    continue

                # build a deploy task
                deploy_task = {
                  'command': 'deploy_and_restart',
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                  'source': os.path.join(service_config.install_location, service_config.unpack_dir, package.packagename),
                  'destination': os.path.join(service_config.install_location, package.packagename),
                  'link_target': os.path.join(service_config.install_location, package.servicename),
                  'tag': package.servicename,
                }

                # clean up install location
                cleanup_tasks.append({
                  'command': 'cleanup',
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                  'path': service_config.install_location,
                  'filespec': '{0}_*'.format(package.servicename),
                  'keepversions': self.config.keep_versions,
                  'tag': package.servicename,
                })

                # Enable or disable daemontools
                if service_config.control_type == 'daemontools':

                    if hasattr(service_config, 'enabled_on_hosts') and (service_config.enabled_on_hosts == 'all' \
                      or hostname in service_config.enabled_on_hosts):

                        daemontools_tasks.append({
                          'command': 'add_daemontools',
                          'remote_host': hostname,
                          'remote_user': self.config.user,
                          'servicename': package.servicename,
                          'unless_exists': '/etc/service/{0}'.format(package.servicename),
                          'tag': package.servicename,
                        })

                    else:
                        self.log.warning('Service will be disabled on {0}'.format(hostname), tag=package.servicename)

                        daemontools_tasks.append({
                          'command': 'remove_daemontools',
                          'remote_host': hostname,
                          'remote_user': self.config.user,
                          'servicename': package.servicename,
                          'if_exists': '/etc/service/{0}'.format(package.servicename),
                          'tag': package.servicename,
                        })

                        # The remaining tasks only apply to services that will are enabled on this host
                        deploy_tasks.append(deploy_task)
                        continue

                # add LB tasks if configured for this service
                lb_hostname, lb_username, lb_password = self.config.get_lb(package.servicename, hostname)

                if lb_hostname and lb_username and lb_password:

                    if hasattr(service_config, 'lb_service'):
                        deploy_task['lb_service'] = service_config.lb_service.format(
                          hostname=hostname.split('.', 1)[0],
                          servicename=package.servicename,
                        )

                        deploy_task.update({
                          'lb_hostname': lb_hostname,
                          'lb_username': lb_username,
                          'lb_password': lb_password,
                        })

                    else:
                        self.log.warning('No lb_service defined for service {0}'.format(package.servicename))
                else:
                    self.log.warning('No load balancer found for {0} on {1}'.format(package.servicename, hostname))

                # add timeout options to deploy task
                for option in ('control_timeout', 'lb_timeout'):
                    if hasattr(service_config, option):
                        deploy_task[option] = getattr(service_config, option)

                control_commands = ['stop_command', 'start_command', 'check_command']

                # add service control options
                for cmd in control_commands:

                    if hasattr(service_config, cmd):
                        deploy_task[cmd] = service_config[cmd].format(
                          servicename=package.servicename,
                          port=service_config['port'],
                        )
                    else:
                        self.log.warning('No {0} configured for service {1}'.format(
                            cmd, package.servicename))

                # cfp service on active cfp host gets deployed separatedly
                if package.servicename == 'cas-cfp-service' and hostname == active_cfp_host:
                    cfp_tasks.append(deploy_task)
                else:
                    deploy_tasks.append(deploy_task)

        if properties_tasks or dbmig_tasks or deploy_tasks:
            doing_deploy_tasks = True
        else:
            doing_deploy_tasks = False

        if upload_tasks:
            task_list['stages'].append({
              'name': 'Upload',
              'concurrency': self.config.non_deploy_concurrency,
              'concurrency_per_host': self.config.non_deploy_concurrency_per_host,
              'tasks': upload_tasks,
            })

        if create_temp_tasks:
            task_list['stages'].append({
              'name': 'Create temp directories',
              'concurrency': self.config.non_deploy_concurrency,
              'concurrency_per_host': self.config.non_deploy_concurrency_per_host,
              'tasks': create_temp_tasks,
            })

        if unpack_tasks:
            task_list['stages'].append({
              'name': 'Unpack',
              'concurrency': self.config.non_deploy_concurrency,
              'concurrency_per_host': self.config.non_deploy_concurrency_per_host,
              'tasks': unpack_tasks,
            })

        if hasattr(self.config, 'graphite') and doing_deploy_tasks and self.config.release:
            doing_deploy_tasks = True
            task_list['stages'].append(self.get_graphite_stage('start'))

        if properties_tasks:

            task_list['stages'].append({
              'name': 'Properties',
              'concurrency': self.config.non_deploy_concurrency,
              'tasks': properties_tasks,
            })

        if daemontools_tasks:

            task_list['stages'].append({
              'name': 'Setting daemontools state',
              'concurrency': self.config.non_deploy_concurrency,
              'tasks': daemontools_tasks,
            })

        if dbmig_tasks:

            task_list['stages'].append({
              'name': 'Database migrations',
              'concurrency': 1,
              'tasks': dbmig_tasks,
            })

        # deploy backend services except for cfp on the active host
        for hostlist in self.config.deployment_order['backend']:
            this_stage, this_stage_tasks = self.get_deploy_stage(deploy_tasks, hostlist)

            if this_stage:
                task_list['stages'].append(this_stage)
                deploy_tasks = [x for x in deploy_tasks if not x in this_stage_tasks]

        # deploy cfp on the active host
        if cfp_tasks:

            task_list['stages'].append({
              'name': 'Deploy cfp service to active host {0}'.format(active_cfp_host),
              'concurrency': 1,
              'tasks': cfp_tasks,
            })

        # deploy frontend services
        for hostlist in self.config.deployment_order['frontend']:
            this_stage, this_stage_tasks = self.get_deploy_stage(deploy_tasks, hostlist)

            if this_stage:
                task_list['stages'].append(this_stage)
                deploy_tasks = [x for x in deploy_tasks if not x in this_stage_tasks]

        if deploy_tasks:

            for deploy_task in deploy_tasks:
                self.log.critical('Leftover task: {0}'.format(deploy_task))

            sys.exit(1)

        if hasattr(self.config, 'graphite') and doing_deploy_tasks:
            task_list['stages'].append(self.get_graphite_stage('end'))

        if remove_temp_tasks:
            task_list['stages'].append({
              'name': 'Remove temp directories',
              'concurrency': self.config.non_deploy_concurrency,
              'concurrency_per_host': self.config.non_deploy_concurrency_per_host,
              'tasks': remove_temp_tasks,
            })

        if cleanup_tasks:
            task_list['stages'].append({
              'name': 'Cleanup',
              'concurrency': self.config.non_deploy_concurrency,
              'concurrency_per_host': self.config.non_deploy_concurrency_per_host,
              'tasks': cleanup_tasks,
            })

        return task_list

    def get_active_cfp(self, hostlist):
        """Find the active cfp server"""

        self.log.info('Determining active cfp host')

        active_host = None
        log_cmd = 'tail -n 1000 /opt/logs/cas-cfp-service.log | grep "Start handling batch with" | grep -v "Start handling batch with 0 events"'

        for hostname in hostlist:
            remote_host = self.get_remote_host(hostname, self.config.user)

            try:
                res = remote_host.execute_remote(log_cmd)
            except (Exception, SystemExit):
                self.log.info('Failed to connect to {0}, skipping check for active cfp host'.format(hostname))
                return None
            else:
                if res.succeeded and res.return_code == 0:
                    self.log.info('cfp service is active on {0}'.format(hostname))
                    return hostname

        self.log.warning('Unable to find active cfp host, will deploy cfp with concurrency'.format(hostlist[0]))
        return None

    def get_deploy_stage(self, tasklist, hostlist):
        """Return a stage based on a list of tasks and a list of hosts"""

        this_stage_tasks = [x for x in tasklist if x['remote_host'] in hostlist]
        this_stage_hosts = ', '.join(sorted(set([x['remote_host'] for x in this_stage_tasks])))

        if not this_stage_tasks:
            self.log.debug('No tasks found for deployment_order group {0}'.format(hostlist))
            return None, None

        tasklist = [x for x in tasklist if not x in this_stage_tasks]

        self.log.info('Found {0} tasks for deployment_order group {1}'.format(len(this_stage_tasks), this_stage_hosts))

        this_task = {
          'name': 'Deploy to hosts {0}'.format(this_stage_hosts),
          'concurrency': self.config.deploy_concurrency,
          'concurrency_per_host': self.config.deploy_concurrency_per_host,
          'tasks': this_stage_tasks,
        }

        return this_task, this_stage_tasks

    def get_graphite_stage(self, metric_suffix):
        """Return a task for send_graphite"""

        task = {
          'command': 'send_graphite',
          'carbon_host': self.config.graphite.carbon_host,
          'metric_name': '.'.join((self.config.graphite.metric_prefix, metric_suffix)),
        }

        stage = {
          'name': 'Send graphite {0}'.format(metric_suffix),
          'concurrency': 1,
          'tasks': [task],
        }

        return stage
