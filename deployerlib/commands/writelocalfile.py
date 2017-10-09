from deployerlib.command import Command


class WriteLocalFile(Command):
    """Write a local file"""

    def initialize(self, filename, content):
        self.filename = filename
        self.content = content
        return True

    def execute(self):

        try:

            with open(self.filename, 'w') as f:
                f.write(self.content)

        except Exception as e:
            self.log.warning('Failed to write file: {}'.format(self.filename))
            return True

        self.log.info('Updated {}'.format(self.filename))

        return True
