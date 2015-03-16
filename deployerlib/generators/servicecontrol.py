from deployerlib.generator import Generator

from deployerlib.exceptions import DeployerException



class ServiceControl(Generator):
    """Stop, start, restart services"""

    def generate(self):

        if self.config.restartservice:
            self.services = self.config.restartservice
            self.action = 'restart'
        elif self.config.disableservice:
            self.services = self.config.disableservice
            self.action = 'disable'
        elif self.config.enableservice:
            self.services = self.config.enableservice
            self.action = 'enable'
        elif self.config.listservices:
            self.services = []
            self.action = 'list'
        else:
            raise DeployerException('No control method was specified')

        task_list = {
          'name': 'Control services',
          'stages': [],
        }

        hosts = []

        if self.config.hosts:
            hosts = self.config.hosts

            if not type(hosts) == list:
                hosts = [hosts]

        if self.action == 'list':
            this_task['command'] = 'list_services'

        for servicename in self.services:
            service_config = self.config.get_with_defaults('service', servicename)
            stage_name = '{0} service {1}'.format(self.action.capitalize(), servicename)
            stage_tasks = []

            if not self.config.hosts:
                hosts = self.config.get_service_hosts(servicename)

            for hostname in hosts:

                self.log.debug('Adding command to {0} service on {1}'.format(
                  self.action, hostname), tag=servicename)

                this_task = {
                  'remote_host': hostname,
                  'remote_user': self.config.user,
                  'tag': servicename,
                }

                control_commands = {}

                for cmd in ['stop_command', 'start_command', 'check_command']:
                    control_commands[cmd] = service_config.get(cmd)

                    if control_commands[cmd]:
                        control_commands[cmd] = control_commands[cmd].format(
                          servicename=servicename,
                          port=service_config['port'],
                        )

                if self.action == 'restart':
                    this_task['command'] = 'restart_service'
                    this_task['stop_command'] = control_commands['stop_command']
                    this_task['start_command'] = control_commands['start_command']
                elif self.action == 'disable':
                    this_task['command'] = 'stop_service'
                    this_task['stop_command'] = control_commands['stop_command']
                    # To do: Substep or other grouping to allow for LB control
                    self.config.skip_lb = True
                # Note: No LB control
                elif self.action == 'enable':
                    this_task['command'] = 'start_service'
                    this_task['start_command'] = control_commands['start_command']
                    # To do: Substep or other grouping to allow for LB control
                    self.config.skip_lb = True

                this_task['check_command'] = control_commands['check_command']

                lb_hostname, lb_username, lb_password = self.config.get_lb(servicename, hostname)

                if not self.config.skip_lb and lb_hostname and lb_username and lb_password:

                    if hasattr(service_config, 'lb_service'):

                        this_task['lb_service'] = service_config.lb_service.format(
                          hostname=hostname.split('.', 1)[0],
                          servicename=servicename,
                        )

                        this_task.update({
                          'lb_hostname': lb_hostname,
                          'lb_username': lb_username,
                          'lb_password': lb_password,
                        })

                    else:
                        self.log.warning('No lb_service defined', tag=servicename)
                else:
                    self.log.warning('No load balancer control for {0}'.format(hostname), tag=servicename)

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
                self.log.warning('No tasks for state "stage_name"', tag=servicename)

        return task_list
