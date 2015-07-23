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
