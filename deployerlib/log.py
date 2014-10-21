import sys
import logging
import logging.handlers

from time import gmtime, strftime
from fabric.colors import red, green, yellow, cyan
from fabric.api import env


level = logging.INFO


class Log(object):

    def __init__(self, instance='DEPLOYER'):

        global level
        self.logger = self.get_logger(instance, level)

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

        formatter = logging.Formatter('%(asctime)s [%(name)-15s] [%(levelname)-7s] %(deployuser)s@%(deployhost)s: %(message)s')

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

    def log(self, message, level):
        """
        Pretty logger with levels and colors for the console.
        If scripts are running as user 'hudson' or 'jenkins' colors are ommited.
        Takes: message (Logger reporting for duty!), level (info, warn, error)
        Gives: formatted message to the console
        """

        if env.host:
            self.logger.log(level, message, extra={'deployhost':env.host, 'deployuser':env.user})
        else:
            self.logger.log(level, message, extra={'deployhost':'*', 'deployuser':'*'})

    def debug(self, message):
        self.log(message, logging.DEBUG)

    def info(self, message):
        self.log(message, logging.INFO)

    def warning(self, message):
        self.log(yellow(message), logging.WARNING)

    def error(self, message):
        self.log(cyan(message), logging.ERROR)

    def critical(self, message):
        self.log(red(message), logging.CRITICAL)


def set_debug(debug=True):

    global level

    if debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
