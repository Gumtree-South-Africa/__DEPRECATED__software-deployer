import os

from deployerlib.log import Log
from deployerlib.generator import Generator


class DemoGenerator(Generator):
    """Build a deployment matrix"""

    def generate(self):

        packages = self.get_packages()
        remote_versions = self.get_remote_versions(packages)

        task_list = {
          'name': 'Aurora deployment',
          'stages': [],
        }

        upload_tasks = []
        create_temp_tasks = []
        properties_tasks = []
        unpack_tasks = []
        dbmig_tasks = []
        deploy_tasks = []
        remove_temp_tasks = []
        cleanup_tasks = []

        properties_done = []

        for package in packages:

            service_config = self.config.get_with_defaults('service', package.servicename)
            hosts = self.config.get_service_hosts(package.servicename)

            for hostname in hosts:

                if not self.config.redeploy and remote_versions.get(package.servicename).get(hostname) \
                  == package.version:
                    self.log.debug('Service {0} is up to date on {1}, skipping'.format(
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
                  'keepversions': 5,
                })

                if not [x for x in create_temp_tasks if x['remote_host'] == hostname and \
                  x['source'] == os.path.join(service_config.install_location, service_config.unpack_dir)]:
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

                if package.servicename == 'cas-properties':

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

                deploy_task = {
                  '_servicename': package.servicename,
                  'command': 'deploy_and_restart',
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                  'source': os.path.join(service_config.install_location, service_config.unpack_dir, package.packagename),
                  'destination': os.path.join(service_config.install_location, package.packagename),
                  'link_target': os.path.join(service_config.install_location, package.servicename),
                  'tag': package.servicename,
                }

                if hasattr(service_config, 'migration_command') and not [x for x in dbmig_tasks \
                  if x['_servicename'] == package.servicename]:

                    self.log.info('Adding DB migrations for {0} on {1}'.format(package.servicename, hostname))

                    dbmig_tasks.append({
                      '_servicename': package.servicename,
                      'command': 'dbmigration',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': service_config.migration_command.format(
                        migration_location=os.path.join(service_config.install_location, service_config.unpack_dir, package.packagename),
                        migration_options='',
                      ),
                      'tag': package.servicename,
                    })

                lb_hostname, lb_username, lb_password = self.config.get_lb(package.servicename, hostname)

                if lb_hostname and lb_username and lb_password:
                    if hasattr(service_config, 'lb_service'):
                        deploy_task['lb_service'] = service_config.lb_service.format(hostname=hostname)

                        deploy_task.update({
                          'lb_hostname': lb_hostname,
                          'lb_username': lb_username,
                          'lb_password': lb_password,
                        })

                    else:
                        self.log.warning('No lb_service defined for service {0}'.format(package.servicename))
                else:
                    self.log.warning('No load balancer found for {0} on {1}'.format(package.servicename, hostname))

                for cmd in ['stop_command', 'start_command', 'check_command']:

                    if hasattr(service_config, cmd):
                        deploy_task[cmd] = service_config[cmd].format(
                          servicename=package.servicename,
                          port=service_config['port'],
                        )
                    else:
                        self.log.warning('No {0} configured for service {1}'.format(
                            cmd, package.servicename))

                deploy_tasks.append(deploy_task)

                # clean up install location
                cleanup_tasks.append({
                  'command': 'cleanup',
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                  'path': service_config.install_location,
                  'filespec': '{0}_*'.format(package.servicename),
                  'keepversions': 5,
                })

        if not upload_tasks and not unpack_tasks and not deploy_tasks:
            self.log.info('No services require deployment')
            return

        sent_graphite = False

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
              'concurrency_per_host': 3,
              'tasks': unpack_tasks,
            })

        if properties_tasks:
            task_list['stages'].append({
              'name': 'Properties',
              'concurrency': 10,
              'concurrency_per_host': 5,
              'tasks': properties_tasks,
            })

        if dbmig_tasks:

            if not sent_graphite:
                sent_graphite = True
                task_list['stages'].append(self.get_graphite_stage('start'))

            for task in dbmig_tasks:
                del task['_servicename']

            task_list['stages'].append({
              'name': 'Database migrations',
              'concurrency': 1,
              'tasks': dbmig_tasks,
            })

        for servicenames in self.config.deployment_order:

            if isinstance(servicenames, basestring):
                servicenames = [servicenames]

            this_stage = [x for x in deploy_tasks if x['_servicename'] in servicenames]

            if not this_stage:
                self.log.debug('No deployment tasks for service {0}'.format(', '.join(servicenames)))
                continue

            deploy_tasks = [x for x in deploy_tasks if not x in this_stage]

            for task in this_stage:
                del task['_servicename']

            if not sent_graphite:
                sent_graphite = True
                task_list['stages'].append(self.get_graphite_stage('start'))

            task_list['stages'].append({
              'name': 'Deploy {0}'.format(', '.join(servicenames)),
              'concurrency': 3,
              'tasks': this_stage,
            })

        if sent_graphite:
            task_list['stages'].append(self.get_graphite_stage('end'))

        if remove_temp_tasks:
            task_list['stages'].append({
              'name': 'Remove temp directories',
              'concurrency': 10,
              'tasks': remove_temp_tasks,
            })

        if cleanup_tasks:
            task_list['stages'].append({
              'name': 'Cleanup',
              'concurrency': 10,
              'concurrency_per_host': 5,
              'tasks': cleanup_tasks,
            })

        if deploy_tasks:
            leftovers = set([x['_servicename'] for x in deploy_tasks])
            raise DeployerException('Leftover tasks - services not specified in deployment order? {0}'.format(
              ', '.join(leftovers)))

        return task_list

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
