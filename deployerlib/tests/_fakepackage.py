import os
import time
import hashlib
import datetime


class FakePackage(object):
    """Create a fake package file to be used for testing"""

    def __init__(self, servicename='test-package', location='/tmp'):
        self.servicename = servicename
        self.location = location

        self.timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
        self.sha = hashlib.sha1(os.urandom(10)).hexdigest()

        self.packagename = '{0}_{1}-{2}'.format(self.servicename, self.sha, self.timestamp)
        self.filename = '{0}.tar.gz'.format(self.packagename)
        self.fullpath = os.path.join(self.location, self.filename)

        with open(self.fullpath, 'w') as f:
            f.close()

    def __del__(self):

        try:
            os.remove(self.fullpath)
        except OSError:
            pass

    def __str__(self):
        return self.fullpath

    def __repr__(self):
        return '{0}(fullpath={1})'.format(self.__class__.__name__, repr(self.fullpath))
