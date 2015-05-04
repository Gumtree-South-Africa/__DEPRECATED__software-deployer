#!/usr/bin/env python2.7

__author__ = 'vlazarenko and yflerko'

# Run this with
# PYTHONPATH=. DJANGO_SETTINGS_MODULE=testsite.settings testsite/tornado_main.py
# Below code to allow us skip action above:
import os
import sys

__my_path__ = os.path.abspath(os.path.dirname(__file__))
if __my_path__ not in sys.path:
    sys.path.append(__my_path__)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "deployerweb.settings")

from tornado.options import options, define, parse_command_line
import django.core.handlers.wsgi
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.wsgi
import tornado.websocket

import logging
import deployerweb.deployhelper as Dhelper

# Bypassing manage.py starts from Django 1.6 and newer
# https://docs.djangoproject.com/en/1.8/intro/tutorial01/#playing-with-the-api
if django.VERSION[1] > 5:
    django.setup()

# Futures required for threading during deployment actions
# import concurrent.futures
import signal
# import time
# import random

# Tornado options, need find better place for them later
define('port', type=int, default=8081, help='server port number (default: 8080)')
define('debug', type=bool, default=True, help='run in debug mode with autoreload (default: True)')
options.log_file_prefix = (__my_path__ + '/logs/tornado_server.log')
options.log_file_max_size = (20*2**10*2**10)
parse_command_line()


MAIN_RUN = True


def signal_handler(signum, frame):
    global MAIN_RUN
    logging.info('exiting...')
    MAIN_RUN = False
    tornado.ioloop.IOLoop.instance().stop()


class Application(tornado.web.Application):
    ''' Main application definition '''

    def __init__(self):
        wsgi_app = tornado.wsgi.WSGIContainer(django.core.handlers.wsgi.WSGIHandler())
        handlers = [
            # (r'/start/', Dhelper.StartHandler),
            (r'/start_deploy/', Dhelper.DeployIt),
            (r'/get_running_jobs/', Dhelper.AnyJobsWeHave),
            (r'/listen/', Dhelper.Md2kHandler),
            ('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
        ]
        settings = dict()
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    ''' Main loop of application '''

    parse_command_line()
    logger = logging.getLogger(__name__)
    logger.info("Tornado server starting...")
    signal.signal(signal.SIGINT, signal_handler)
    server = tornado.httpserver.HTTPServer(Application())
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
