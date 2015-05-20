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

# WebDeployment parameter to enable/disable stdoutput for deployer
is_web = False

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


def get_my_loggers():
    '''
        Logger manipulation hook for Web deployment tool:
        Return all loggers instances as Dict() created by this class
    '''
    global LogDict
    return LogDict


def clean_my_loggers():
    '''
        Logger manipulation hook for Web deployment tool:
        Clean all logger instances created by this class
    '''
    global LogDict
    for logname in LogDict.keys():
        del logging.Logger.manager.loggerDict[logname]
        del LogDict[logname]


def set_is_web():
    '''
        Logger manipulation hook for Web deployment tool:
        Set global variable 'is_web' to disable stdout logging for deployer
    '''
    global is_web
    is_web = True


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

        formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] [%(name)-15s] [%(remote)s] [%(tag)s] %(message)s')

        global is_web
        if not is_web:
            console = logging.StreamHandler(sys.stdout)
            console.setLevel(level)
            console.setFormatter(formatter)
            logger.addHandler(console)

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
