from deployerlib.generator import Generator
from deployerlib.exceptions import DeployerException


class ServiceControl(Generator):
    """Stop, start, restart services"""

    def generate(self):

        if self.config.listservices:
            self.list_services()
        elif self.config.restartservice:
            self.control_services('restart', self.config.restartservice)
        elif self.config.disableservice:
            self.control_services('stop', self.config.disableservice)
        elif self.config.enableservice:
            self.control_services('start', self.config.enableservice)
        else:
            raise DeployerException('No control method was specified')

        return self.tasklist.generate()

    def list_services(self):
        """List the services running on a set of hosts"""

        if not self.config.hosts:
            raise DeployerException('Please specify one or more hosts using the --hosts flag')

        stage_name = 'List services'
        self.tasklist.create_stage(stage_name, concurrency=1)

        for hostname in self.config.hosts:
            self.tasklist.add_hosts(stage_name, hostname)
            self.tasklist.add(stage_name, {
              'command': 'listdirectory',
              'directory': '/etc/service/',
              'remote_host': hostname,
              'remote_user': self.config.user,
            })

    def control_services(self, action, servicenames, hosts=[]):
        """Restart the specified services"""

        base_stage_name = 'Restart {0}'.format(', '.join(servicenames))

        for servicename in servicenames:
            for stage_num, hostlist in enumerate(self._get_service_stages(servicename)):
                this_stage_name = '{0}|stage{1}'.format(base_stage_name, stage_num)

                for hostname in hostlist:
                    control_type = self.get_control_type(servicename, hostname)

                    if not control_type:
                        self.log.debug('Not controlling {0} on {1}'.format(servicename, hostname))
                        continue

                    self.log.debug('Adding {0} commands for {1} on {2}'.format(action, servicename, hostname))
                    stop, start = self._deploy_subtask_svc_control(hostname, servicename, control_type)

                    if self.config.ignore_lb:
                        disable_lb, enable_lb = [], []
                    else:
                        disable_lb, enable_lb = self._deploy_subtask_lb_control(hostname, servicename)

                    if action == 'stop':
                        task = disable_lb + stop
                    elif action == 'start':
                        task = start + enable_lb
                    elif action == 'restart':
                        task = disable_lb + stop + start + enable_lb
                    else:
                        raise DeployerException('Unknown action for control_services: {0}'.format(action))

                    self.tasklist.create_stage(this_stage_name, concurrency=self.config.deploy_concurrency, concurrency_per_host=self.config.deploy_concurrency_per_host)
                    self.tasklist.add_hosts(this_stage_name, hostname)
                    self.tasklist.add(this_stage_name, task)
