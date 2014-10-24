from deployerlib.log import Log
from deployerlib.matrixhelper import MatrixHelper
from deployerlib.exceptions import DeployerException


class DemoMatrix(object):
    """Build a deployment matrix"""

    def __init__(self, config):
        self.log = Log(self.__class__.__name__)
        self.config = config
        self.matrixhelper = MatrixHelper(config)
        self.services = self.matrixhelper.get_services()
        self.remote_versions = self.matrixhelper.get_remote_versions(self.services)

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

        for service in self.services:

            for host in service.hosts:

                if not self.config.redeploy and self.remote_versions.get(service.servicename).get(host.hostname) \
                  == service.version:
                    self.log.debug('Service {0} is up to date on {1}, skipping'.format(
                      service.servicename, host.hostname))
                    continue

                upload_tasks.append({
                  'command': 'upload',
                  'remote_host': host.hostname,
                  'remote_user': self.config.user,
                  'source': service.fullpath,
                  'destination': service.upload_location,
                })

                unpack_tasks.append({
                  'command': 'unpack',
                  'remote_host': host.hostname,
                  'remote_user': self.config.user,
                  'source': service.remote_filename,
                  'destination': service.unpack_dir,
                })

                deploy_task = {
                  '_servicename': service.servicename,
                  'command': 'deploy_and_restart',
                  'remote_host': host.hostname,
                  'remote_user': self.config.user,
                  'source': service.unpack_destination,
                  'destination': service.install_destination,
                  'link_target': service.symlink,
                }

                if hasattr(service.service_config, 'migration_command') and not [x for x in dbmig_tasks \
                  if x['_servicename'] == service.servicename]:

                    self.log.info('Adding DB migrations for {0} on {1}'.format(service.servicename, host.hostname))

                    dbmig_tasks.append({
                      '_servicename': service.servicename,
                      'command': 'dbmigration',
                      'remote_host': host.hostname,
                      'remote_user': self.config.user,
                      'source': service.service_config.migration_command.format(
                        migration_location=service.service_config.migration_location, migration_options=''),
                    })

                lb_hostname, lb_username, lb_password = self.config.get_lb(service.servicename, host.hostname)

                if lb_hostname and lb_username and lb_password:
                    if hasattr(service, 'lb_service'):
                        deploy_task['lb_service'] = service.lb_service.format(hostname=host.hostname)

                        deploy_task.update({
                          'lb_hostname': lb_hostname,
                          'lb_username': lb_username,
                          'lb_password': lb_password,
                        })

                    else:
                        self.log.warning('No lb_service defined for service {0}'.format(service.servicename))
                else:
                    self.log.warning('No load balancer found for {0} on {1}'.format(service.servicename, host.hostname))

                if hasattr(service, 'control_commands'):

                    for cmd in ['stop', 'start', 'check']:
                        if cmd in service.control_commands:
                            deploy_task['{0}_command'.format(cmd)] = service.control_commands[cmd]

                deploy_tasks.append(deploy_task)

                if not [x for x in create_temp_tasks if x['remote_host'] == host.hostname and \
                  x['source'] == service.unpack_dir]:
                    create_temp_tasks.append({
                      'command': 'createdirectory',
                      'remote_host': host.hostname,
                      'remote_user': self.config.user,
                      'source': service.unpack_dir,
                      'clobber': True,
                    })

                    remove_temp_tasks.append({
                      'command': 'removefile',
                      'remote_host': host.hostname,
                      'remote_user': self.config.user,
                      'source': service.unpack_dir,
                    })

        if not upload_tasks and not unpack_tasks and not deploy_tasks:
            self.log.info('No services require deployment')
            return

        if upload_tasks:
            task_list['stages'].append({
              'name': 'Upload',
              'parallel': 10,
              'tasks': upload_tasks,
            })

        if create_temp_tasks:
            task_list['stages'].append({
              'name': 'Create temp directories',
              'parallel': 10,
              'tasks': create_temp_tasks,
            })

        if unpack_tasks:
            task_list['stages'].append({
              'name': 'Unpack',
              'parallel': 10,
              'tasks': unpack_tasks,
            })

        if dbmig_tasks:
            for task in dbmig_tasks:
                del task['_servicename']

            task_list['stages'].append({
              'name': 'Database migrations',
              'parallel': 1,
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
              'parallel': 3,
              'tasks': this_stage,
            })

        if remove_temp_tasks:
            task_list['stages'].append({
              'name': 'Remove temp directories',
              'parallel': 10,
              'tasks': remove_temp_tasks,
            })

        if deploy_tasks:
            leftovers = set([x['_servicename'] for x in deploy_tasks])
            raise DeployerException('Leftover tasks - services not specified in deployment order? {0}'.format(
              ', '.join(leftovers)))

        return task_list
