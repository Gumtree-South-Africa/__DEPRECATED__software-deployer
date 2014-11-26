from deployerlib.command import Command


class AddDaemontools(Command):

    def initialize(self, remote_host, servicename, update_service='/usr/sbin/update-service',
      service_dir='/etc/service', supervise_dir='/var/lib/supervise', unless_exists=None):

        self.update_service = update_service
        self.service_dir = service_dir
        self.supervise_dir = supervise_dir
        self.unless_exists = unless_exists

        return True

    def execute(self):

        if self.unless_exists:

            if self.remote_host.file_exists(self.unless_exists):
                self.log.debug('Skipping daemontools registration, file exists: {0}'.format(
                  self.unless_exists))
                return True

            self.log.debug('{0} does not exist, continuing with service registration'.format(
              self.unless_exists))

        res = self.remote_host.execute_remote('{0} --check {1}'.format(
          self.update_service, self.servicename))

        if res.succeeded:
            self.log.info('Daemontools service {0} is already registered'.format(self.servicename))
            return True

        res = self.remote_host.execute_remote('{0} --add {1}/{2} {2}'.format(
            self.update_service, self.supervise_dir, self.servicename), use_sudo=True)

        if res.succeeded:
            self.log.info('Registered daemontools service {0}'.format(self.servicename))
            return True
        else:
            self.log.critical('Failed to register daemontools service {0}'.format(self.servicename))
            return False
