import sys
import logging
import logging.handlers

from fabric.colors import red, green, yellow, cyan, blue, magenta
from fabric.api import env

from deployerlib.exceptions import DeployerException

# Default level
level = logging.INFO
logfile = ''
LogDict = {}

# Add level VERBOSE
logging.VERBOSE = 15
logging.addLevelName(logging.VERBOSE, 'VERBOSE')

# Add level HIDEBUG
logging.HIDEBUG = 5
logging.addLevelName(logging.HIDEBUG, 'HIDEBUG')

myloggerDict = logging.Manager


def set_level(new_level):

    global level
    level = new_level


def set_logfile(new_logfile):

    global logfile
    logfile = new_logfile


class Log(object):

    def __init__(self, instance='DEPLOYER', tag=''):
        global level
        global logfile

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

        global logfile

        logger = logging.getLogger(instance)
        logger.setLevel(1)

        # console = logging.StreamHandler(sys.stdout)
        # console.setLevel(level)

        formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] [%(name)-15s] [%(remote)s] [%(tag)s] %(message)s')

        # console.setFormatter(formatter)
        # logger.addHandler(console)

        if logfile:

            try:
                logfile_h = logging.FileHandler(logfile)
            except IOError, e:
                raise DeployerException("Can not open logfile, permission denied?")

            if level > logging.DEBUG:
                logfile_level = logging.DEBUG
            else:
                logfile_level = level

            logfile_h.setLevel(logfile_level)

            logfile_h.setFormatter(formatter)
            logger.addHandler(logfile_h)

        global LogDict
        LogDict.update({instance: logger})
        return logger

    def get_logfile(self):
        global logfile
        return logfile

    def log(self, message, level, tag=''):
        """Pretty logger with levels and colors"""

        host = '*'
        if env.host:
            host = env.host

        if not tag:
            tag = self.tag

        self.logger.log(level, message, extra={'tag': tag, 'remote': host})

    def hidebug(self, message, tag=''):
        self.log(message, logging.HIDEBUG, tag)

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
