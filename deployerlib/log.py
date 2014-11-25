import sys
import logging
import logging.handlers

from time import gmtime, strftime
from fabric.colors import red, green, yellow, cyan, blue, magenta
from fabric.api import env


level = logging.INFO
logging.VERBOSE = 15
logging.addLevelName(logging.VERBOSE, 'VERBOSE')



def set_level(new_level):

    global level
    level = new_level


class Log(object):

    def __init__(self, instance='DEPLOYER', tag=''):
        global level

        self.logger = self.get_logger(instance, level)
        self.instance = instance
        if not tag:
            tag = '*'
        self.tag = tag

    def get_logger(self, instance, level):
        """If a logger exists for this instance, return it; otherwise create a new logger"""

        if instance in logging.Logger.manager.loggerDict:
            return logging.Logger.manager.loggerDict[instance]
        else:
            return self.create_logger(instance, level)

    def create_logger(self, instance, level):
        """Create and return a new logger"""

        logger = logging.getLogger(instance)
        logger.setLevel(level)

        d = strftime("%Y-%m-%d-%H:%M:%S", gmtime())

        console = logging.StreamHandler(sys.stdout)
        console.setLevel(level)

        formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] [%(name)-15s] [%(remote)s] [%(tag)s] %(message)s')

        console.setFormatter(formatter)
        logger.addHandler(console)

#        # silently create log directory
#        try:
#            auroralib.util.DUtil.mkdir_p('/opt/log')
#        except IOError, e:
#            raise DBailException("Can not create logging directory /opt/log. Permission denied?")
#
#        try:
#            logfile = logging.FileHandler('/opt/log/deployer-%s.log' % d)
#        except IOError, e:
#            raise DBailException("Can not open logfile, permission denied?")
#
#        logfile.setLevel(logging.DEBUG)
#
#        logfile.setFormatter(formatter)
#        logger.addHandler(logfile)
#        #logger.handlers[0].doRollover()  # we want a new log each time we deploy something

        return logger

    def log(self, message, level, tag=''):
        """
        Pretty logger with levels and colors for the console.
        If scripts are running as user 'hudson' or 'jenkins' colors are ommited.
        Takes: message (Logger reporting for duty!), level (info, warn, error)
        Gives: formatted message to the console
        """

        host = '*'
        user = '*'
        if env.host:
            host = env.host
            if env.user:
                user = env.user

        if self.logger.isEnabledFor(logging.DEBUG):
            remote = '{0}@{1}'.format(user,host)
        else:
            remote = host

        if not tag:
            tag = self.tag

        self.logger.log(level, message, extra={'tag': tag, 'remote': remote})

    def debug(self, message, tag=''):
        self.log(message, logging.DEBUG, tag)

    def verbose(self, message, tag=''):
        self.log(message, logging.VERBOSE, tag)

    def info(self, message, tag=''):
        self.log(message, logging.INFO, tag)

    def warning(self, message, tag=''):
        self.log(yellow(message), logging.WARNING, tag)

    def error(self, message, tag=''):
        self.log(cyan(message), logging.ERROR, tag)

    def critical(self, message, tag=''):
        self.log(red(message), logging.CRITICAL, tag)
