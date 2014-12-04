from deployerlib.generator import Generator


class TestGenerator(Generator):

    def generate(self):

        self.log.info('Generating test task list')

        task = {
          'command': 'test_command',
          'message': 'Hello World',
        }

        stage = {
          'name': 'Test stage',
          'concurrency': 1,
          'tasks': [task],
        }

        tasklist = {
          'name': 'Test Generator',
          'stages': [stage],
        }

        return tasklist
