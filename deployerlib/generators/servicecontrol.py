from deployerlib.log import Log

from deployerlib.exceptions import DeployerException



class ServiceControl(object):
    """Stop, start, restart services"""

    def __init__(self, config):
        self.log = Log(self.__class__.__name__)
        self.config = config

        if config.restartservice:
            self.services = config.restartservice
            self.action = 'restart'
        elif config.disableservice:
            self.services = config.disableservice
            self.action = 'disable'
        elif config.enableservice:
            self.services = config.enableservice
            self.action = 'enable'
        else:
            raise DeployerException('No control method was specified')

    def generate(self):

        task_list = {
          'name': 'Control services',
          'stages': [],
        }

        for service in self.services:
            service_config = self.config.get_with_defaults('service', service)
            hosts = self.config.get_service_hosts(service)
            stage_name = '{0} service {1}'.format(self.action.capitalize(), service)
            stage_tasks = []

            for hostname in hosts:

                self.log.debug('Adding command to {0} service {1} on {2}'.format(
                  self.action, service, hostname))

                this_task = {
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                }

                control_commands = {}

                for cmd in ['stop_command', 'start_command', 'check_command']:
                    control_commands[cmd] = service_config.get(cmd)

                    if control_commands[cmd]:
                        control_commands[cmd] = control_commands[cmd].format(
                          servicename=service,
                          port=service_config['port'],
                        )

                if self.action == 'restart':
                    this_task['command'] = 'restart_service'
                    this_task['stop_command'] = control_commands['stop_command']
                    this_task['start_command'] = control_commands['start_command']
                elif self.action == 'disable':
                    this_task['command'] = 'control_service'
                    this_task['source'] = control_commands['stop_command']
                    this_task['want_state'] = 2
                elif self.action == 'enable':
                    this_task['command'] = 'control_service'
                    this_task['source'] = control_commands['start_command']

                this_task['check_command'] = control_commands['check_command']


                lb_hostname, lb_username, lb_password = self.config.get_lb(service, hostname)

                if not self.config.skip_lb and lb_hostname and lb_username and lb_password:
                    if hasattr(service_config, 'lb_service'):
                        this_task['lb_service'] = service_config.lb_service.format(
                          hostname=hostname.split('.', 1)[0],
                          servicename=service,
                        )

                        this_task.update({
                          'lb_hostname': lb_hostname,
                          'lb_username': lb_username,
                          'lb_password': lb_password,
                        })

                    else:
                        self.log.warning('No lb_service defined for service {0}'.format(service))
                else:
                    self.log.warning('No load balancer found for {0} on {1}'.format(service, hostname))

                for key in this_task.keys():

                    if key is None:
                        this_task.pop(key)

                stage_tasks.append(this_task)

            if stage_tasks:

                task_list['stages'].append({
                  'name': stage_name,
                  'concurrency': self.config.parallel,
                  'tasks': stage_tasks,
                })

            else:
                self.log.warning('No tasks for state "stage_name"')

        return task_list