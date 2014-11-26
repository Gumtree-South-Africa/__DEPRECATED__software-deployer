from deployerlib.command import Command


class RemoveDaemontools(Command):

    def initialize(self, remote_host, servicename, update_service='/usr/sbin/update-service',
      service_dir='/etc/service', supervise_dir='/var/lib/supervise', if_exists=None):

        self.update_service = update_service
        self.service_dir = service_dir
        self.supervise_dir = supervise_dir
        self.if_exists = if_exists

        return True

    def execute(self):

        if self.if_exists:

            if not self.remote_host.file_exists(self.if_exists):
                self.log.debug('Skipping daemontools removal, file is not present: {0}'.format(
                  self.if_exists))
                return True

            self.log.debug('{0} does not exist, continuing with service removal'.format(
              self.if_exists))

        res = self.remote_host.execute_remote('{0} --check {1}'.format(
          self.update_service, self.servicename))

        if res.failed:
            self.log.info('Daemontools service {0} is already unregistered'.format(self.servicename))
            return True

        res = self.remote_host.execute_remote('{0} --remove {1}/{2} {2}'.format(
            self.update_service, self.supervise_dir, self.servicename), use_sudo=True)

        if res.succeeded:
            self.log.info('Removed daemontools service {0}'.format(self.servicename))
            return True
        else:
            self.log.critical('Failed to remove daemontools service {0}: {1}'.format(self.servicename, res))
            return False
