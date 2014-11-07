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

        task_list = {
          'name': 'iCAS deployment',
          'stages': [],
        }

        upload_tasks = []
        create_temp_tasks = []
        unpack_tasks = []
        dbmig_tasks = []
        properties_tasks = []
        deploy_tasks = []
        cfp_tasks = []
        remove_temp_tasks = []

        tempdir_done = []
        migration_done = []
        properties_done = []

        active_cfp_host = self.get_active_cfp(self.config.get_service_hosts('cas-cfp-service'))
        self.log.info('Active cfp server is {0}'.format(active_cfp_host))

        for package in packages:
            service_config = self.config.get_with_defaults('service', package.servicename)

            if not service_config:
                raise DeployerException('Unknown service: {0}'.format(package.servicename))

            for hostname in self.config.get_service_hosts(package.servicename):

                upload_tasks.append({
                  'command': 'upload',
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                  'source': package.fullpath,
                  'destination': service_config.destination,
                })

                unpack_tasks.append({
                  'command': 'unpack',
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                  'source': os.path.join(service_config.destination, package.filename),
                  'destination': os.path.join(service_config.install_location, service_config.unpack_dir),
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
                if hasattr(service_config, 'migration_command') and not package.servicename in migration_done:
                    migration_done.append(package.servicename)

                    dbmig_tasks.append({
                      'command': 'dbmigration',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': service_config.migration_command.format(
                        unpack_location=os.path.join(service_config.install_location, service_config.unpack_dir, package.packagename),
                        migration_options='',
                      ),
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
                          'destination': '{0}/'.format(service_config.properties_location),
                          'continue_if_exists': True,
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
                }

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

                # add service control options
                for cmd in ['stop_command', 'start_command', 'check_command']:

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

        if upload_tasks:
            task_list['stages'].append({
              'name': 'Upload',
              'concurrency': 10,
              'concurrency_per_host': 5,
              'tasks': upload_tasks,
            })

        if create_temp_tasks:
            task_list['stages'].append({
              'name': 'Create temp directories',
              'concurrency': 10,
              'concurrency_per_host': 5,
              'tasks': create_temp_tasks,
            })

        if unpack_tasks:
            task_list['stages'].append({
              'name': 'Unpack',
              'concurrency': 10,
              'concurrency_per_host': 5,
              'tasks': unpack_tasks,
            })

        if properties_tasks:

            task_list['stages'].append({
              'name': 'Properties',
              'concurrency': 10,
              'tasks': properties_tasks,
            })

        if dbmig_tasks:

            task_list['stages'].append({
              'name': 'Database migrations',
              'concurrency': 1,
              'tasks': dbmig_tasks,
            })

        # deploy backend services except for cfp on the active host
        for hostlist in self.config.deployment_order['backend']:
            this_stage, this_stage_tasks = self.get_stage(deploy_tasks, hostlist)

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
            this_stage, this_stage_tasks = self.get_stage(deploy_tasks, hostlist)

            if this_stage:
                task_list['stages'].append(this_stage)
                deploy_tasks = [x for x in deploy_tasks if not x in this_stage_tasks]

        if deploy_tasks:

            for deploy_task in deploy_tasks:
                self.log.critical('Leftover task: {0}'.format(deploy_task))

            sys.exit(1)

        if remove_temp_tasks:
            task_list['stages'].append({
              'name': 'Remove temp directories',
              'concurrency': 10,
              'tasks': remove_temp_tasks,
            })

        return task_list

    def get_active_cfp(self, hostlist):
        """Find the active cfp server"""

        # placeholder
        import random
        return random.choice(hostlist)

    def get_stage(self, tasklist, hostlist):
        """Return a stage based on a list of tasks and a list of hosts"""

        this_stage_tasks = [x for x in tasklist if x['remote_host'] in hostlist]
        this_stage_hosts = ', '.join(hostlist)

        if not this_stage_tasks:
            self.log.warning('No tasks found for deployment_order group {0}'.format(this_stage_hosts))
            return None, None

        tasklist = [x for x in tasklist if not x in this_stage_tasks]

        self.log.info('Found {0} tasks for deployment_order group {1}'.format(len(this_stage_tasks), this_stage_hosts))

        this_task = {
          'name': 'Deploy to hosts {0}'.format(this_stage_hosts),
          'concurrency': 10,
          'concurrency_per_host': 3,
          'tasks': this_stage_tasks,
        }

        return this_task, this_stage_tasks
