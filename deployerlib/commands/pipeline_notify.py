import urllib2

from deployerlib.command import Command

class PipelineNotify(Command):
    """Notify pipeline"""

    def initialize(self, url, proxy=None, continue_on_fail=True):
        self.url = url
        self.proxy = proxy
        self.continue_on_fail = continue_on_fail
        return True

    def execute(self):
        self.log.info("Calling %s on pipeline..." % self.url)
        if self.proxy:
            proxy_support = urllib2.ProxyHandler({ "http" : self.proxy })
            opener = urllib2.build_opener(proxy_support)
        else:
            opener = urllib2.build_opener()

        try:
            opener.open(self.url)
            return True
        except:
            msg = "Could not notify pipeline!"
            if self.continue_on_fail:
                self.log.warning(msg)
                return True
            else:
                self.log.critical(msg)
                return False

