import os

from deployerlib.log import Log
from deployerlib.generator import Generator
from deployerlib.exceptions import DeployerException


class AuroraGenerator(Generator):
    """Aurora task list generator"""

    def generate(self):
        """Build the task list"""

        packages = self.get_packages()
        if not self.config.redeploy:
            remote_versions = self.get_remote_versions(packages)

        task_list = {
          'name': 'Aurora deployment',
          'stages': [],
        }

        upload_tasks = []
        create_temp_tasks = []
        unpack_tasks = []
        props_tasks = []
        dbmig_tasks = []
        deploy_tasks = []
        remove_temp_tasks = []

        for package in packages:

            servicename = package.servicename
            service_config = self.config.get_with_defaults('service', servicename)
            hosts = self.config.get_service_hosts(servicename)

            for hostname in hosts:

                if not self.config.redeploy and remote_versions.get(servicename).get(hostname) \
                  == package.version:
                    self.log.info('version is up to date on {0}, skipping'.format(hostname), tag=servicename)
                    continue

                upload_tasks.append({
                  'tag': servicename,
                  'command': 'upload',
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                  'source': package.fullpath,
                  'destination': service_config.destination,
                })

                unpack_tasks.append({
                  'tag': servicename,
                  'command': 'unpack',
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                  'source': os.path.join(service_config.destination, package.filename),
                  'destination': os.path.join(service_config.install_location, service_config.unpack_dir),
                })

                if service_config.control_type == 'props':
                    props_tasks.append({
                      'tag': servicename,
                      'command': 'copyfile',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': '{0}/*'.format(os.path.join(service_config.install_location,
                          service_config.unpack_dir, package.packagename, self.config.environment)),
                      'destination': '{0}/'.format(service_config.properties_location),
                      'continue_if_exists': True,
                      'recursive': True,
                    })

                if service_config.control_type == 'daemontools':
                    deploy_task = {
                      'tag': servicename,
                      'command': 'deploy_and_restart',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': os.path.join(service_config.install_location, service_config.unpack_dir, package.packagename),
                      'destination': os.path.join(service_config.install_location, package.packagename),
                      'link_target': os.path.join(service_config.install_location, servicename),
                    }

                    if hasattr(service_config, 'migration_command') and not [x for x in dbmig_tasks \
                      if x['tag'] == servicename]:

                        self.log.info('Adding DB migrations to be run on {0}'.format(hostname), tag=servicename)

                        dbmig_tasks.append({
                          'tag': servicename,
                          'command': 'dbmigration',
                          'remote_host': hostname,
                          'remote_user': self.config.user,
                          'source': service_config.migration_command.format(
                              migration_location=os.path.join(service_config.install_location, service_config.unpack_dir, package.packagename,
                                  'db/migrations'),
                              migration_options='',
                              properties_location=service_config.properties_location,
                              ),
                          })

                    if '.' in servicename:
                        shortservicename = servicename.rsplit(".", 1)[1].replace("-server", "")
                    else:
                        shortservicename = service

                    if '.' in hostname:
                        shorthostname = hostname.split(".", 1)[0]
                    else:
                        shorthostname = hostname

                    if hasattr(service_config, 'lb_service'):
                        lb_service = service_config.lb_service.format(
                                hostname=shorthostname,
                                servicename=shortservicename,
                                )
                    else:

                        if self.config.environment == "production":
                            lb_service = self.config.platform + "_" +  shortservicename + "_" +  hostname.split(".", 1)[0] + "." + self.config.platform
                        elif self.config.environment == "lp":
                            lb_service = self.config.platform + "_" +  shortservicename + "_" +  hostname.split(".", 1)[0] + "." + self.config.platform + self.config.environment
                        else:
                            lb_service = self.config.platform + "_" +  shortservicename + "_" +  hostname.split(".", 1)[0]

                        self.log.info('Generated lb_service={0}'.format(repr(lb_service)))

                    lb_hostname, lb_username, lb_password = self.config.get_lb(servicename, hostname)

                    if lb_hostname and lb_username and lb_password:
                        deploy_task['lb_service'] = lb_service

                        deploy_task.update({
                          'lb_hostname': lb_hostname,
                          'lb_username': lb_username,
                          'lb_password': lb_password,
                        })

                    else:
                        self.log.warning('No load balancer found for service on {0}'.format(hostname), tag=servicename)

                    for option in ('control_timeout', 'lb_timeout'):
                        if hasattr(service_config, option):
                            deploy_task[option] = getattr(service_config, option)

                    for cmd in ['stop_command', 'start_command', 'check_command']:

                        if hasattr(service_config, cmd):
                            deploy_task[cmd] = service_config[cmd].format(
                              servicename=servicename,
                              port=service_config['port'],
                            )
                        else:
                            self.log.warning('No {0} configured'.format(cmd), tag=servicename)

                    deploy_tasks.append(deploy_task)

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
            # end for hostname in hosts:
        # end for package in packages:

        if not upload_tasks and not unpack_tasks and not deploy_tasks:
            self.log.info('No services require deployment')
            return

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

        if props_tasks:
            task_list['stages'].append({
              'name': 'Deploy properties for environment {0}'.format(self.config.environment),
              'concurrency': 10,
              'tasks': props_tasks,
            })

        if dbmig_tasks:
            task_list['stages'].append({
              'name': 'Database migrations',
              'concurrency': 1,
              'tasks': dbmig_tasks,
            })

        for servicenames in self.config.deployment_order:

            if isinstance(servicenames, basestring):
                servicenames = [servicenames]

            this_stage = [x for x in deploy_tasks if x['tag'] in servicenames]

            if not this_stage:
                self.log.debug('No deployment tasks for service(s) {0}'.format(', '.join(servicenames)))
                continue

            deploy_tasks = [x for x in deploy_tasks if not x in this_stage]

            to_deploy = []
            for x in this_stage:
                if x['tag'] not in to_deploy:
                    to_deploy.append(x['tag'])

            task_list['stages'].append({
              'name': 'Deploy {0}'.format(', '.join(to_deploy)),
              'concurrency': 3,
              'tasks': this_stage,
            })

        if remove_temp_tasks:
            task_list['stages'].append({
              'name': 'Remove temp directories',
              'concurrency': 10,
              'tasks': remove_temp_tasks,
            })

        if deploy_tasks:
            leftovers = set([x['tag'] for x in deploy_tasks])
            raise DeployerException('Leftover tasks - services not specified in deployment order? {0}'.format(
              ', '.join(leftovers)))

        return task_list
