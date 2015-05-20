# -*- coding: utf-8 -*-

__author__ = 'vlazarenko'


import logging
from django.conf import settings


def get_logger(name, size=30):
    logger = logging.getLogger('%s logger' % name)
    if not len(logger.handlers):
        logger.setLevel(logging.DEBUG)
        fh = logging.handlers.RotatingFileHandler(settings.BASE_DIR + '/logs/%s.log' % name, maxBytes=size*2**20)  # default size - 30 Mb
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [line:%(lineno)s] [%(pathname)s] [%(funcName)s] %(message)s'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger
