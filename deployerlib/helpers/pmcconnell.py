import os

from deployerlib.log import Log
from deployerlib.matrixhelper import MatrixHelper
from deployerlib.exceptions import DeployerException


class DemoMatrix(object):
    """Build a deployment matrix"""

    def __init__(self, config):
        self.log = Log(self.__class__.__name__)
        self.config = config
        self.matrixhelper = MatrixHelper(config)
        self.packages = self.matrixhelper.get_packages()
        self.remote_versions = self.matrixhelper.get_remote_versions(self.packages)

    def build_matrix(self):

        task_list = {
          'name': 'Aurora deployment',
          'stages': [],
        }

        upload_tasks = []
        create_temp_tasks = []
        unpack_tasks = []
        dbmig_tasks = []
        deploy_tasks = []
        remove_temp_tasks = []

        for package in self.packages:

            service_config = self.config.get_with_defaults('service', package.servicename)
            hosts = self.config.get_service_hosts(package.servicename)

            for hostname in hosts:

                if not self.config.redeploy and self.remote_versions.get(package.servicename).get(hostname) \
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
                })

                unpack_tasks.append({
                  'command': 'unpack',
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                  'source': os.path.join(service_config.destination, package.filename),
                  'destination': os.path.join(service_config.install_location, self.config.unpack_dir),
                })

                deploy_task = {
                  '_servicename': package.servicename,
                  'command': 'deploy_and_restart',
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                  'source': os.path.join(service_config.install_location, self.config.unpack_dir, package.packagename),
                  'destination': os.path.join(service_config.install_location, package.packagename),
                  'link_target': os.path.join(service_config.install_location, package.servicename),
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
                        migration_location=service_config.migration_location, migration_options=''),
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

                if not [x for x in create_temp_tasks if x['remote_host'] == hostname and \
                  x['source'] == os.path.join(service_config.install_location, self.config.unpack_dir)]:
                    create_temp_tasks.append({
                      'command': 'createdirectory',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': os.path.join(service_config.install_location, self.config.unpack_dir),
                      'clobber': True,
                    })

                    remove_temp_tasks.append({
                      'command': 'removefile',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': os.path.join(service_config.install_location, self.config.unpack_dir),
                    })

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

        if dbmig_tasks:
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

            task_list['stages'].append({
              'name': 'Deploy {0}'.format(', '.join(servicenames)),
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
            leftovers = set([x['_servicename'] for x in deploy_tasks])
            raise DeployerException('Leftover tasks - services not specified in deployment order? {0}'.format(
              ', '.join(leftovers)))

        return task_list
