from deployerlib.command import Command
from deployerlib.commands import copyfile


class DeployProperties(Command):
    """Command to deploy properties"""

    def initialize(self, remote_host, source, destination, version):

        self.subcommand = copyfile.CopyFile(
            remote_host=remote_host,
            source=source,
            destination=destination,
            recursive=True,
            continue_if_exists=True,
            tag=self.tag,
        )

        self.version = version

        return True

    def __repr__(self):
        return '{0}(remote_host={1} tag={2})'.format(self.__class__.__name__,
          repr(self.remote_host.hostname), repr(self.tag))

    def execute(self):
        """Copy properties files and update properties_version"""

        subcommand = self.subcommand
        res = subcommand.execute()

        if not res:
            self.log.critical('{0} subcommand {1} failed'.format(
              self.__class__.__name__, subcommand.__class__.__name__))
            return False

        version = self.version
        destination = self.destination
        self.log.info("Updating installed properties version file to: %s" % version)
        res = self.remote_host.execute_remote('echo {0} > {1}/properties_version'.format(version,destination))

        if res.failed:
            self.log.critical('Failed to update properties_version file in {0}: {1}'.format(
              destination, res))

        return res.succeeded
