from deployerlib.generator import Generator


class ListServices(Generator):

    def generate(self):

        self.log.info('Generating test task list')

        tasks = []
        for host in self.config.hosts:
            tasks.append({
              'command': 'listdirectory',
              'directory': '/etc/service/',
              'remote_host': host,
              'remote_user': self.config.user,
            })

        stage = {
          'name': 'Listing stage',
          'concurrency': 1,
          'tasks': tasks,
        }

        tasklist = {
          'name': 'Service List Generator',
          'stages': [stage],
        }

        return tasklist
