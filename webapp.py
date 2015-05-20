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
from django.conf import settings

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
# to Run it in debug mode use flag '--debug=True --logging=debug'
define('port', type=int, default=8080, help='server port number (default: 8080)')
define('debug', type=bool, default=False, help='run in debug mode with autoreload (default: True)')
options.log_file_prefix = (settings.LOG_DIR + '/tornado_server.log')  # default file size 100Mb and with 10 files retention (1GB of logs)


def signal_handler(signum, frame):
    logging.info('exiting...')
    tornado.ioloop.IOLoop.instance().stop()


class Application(tornado.web.Application):
    ''' Main application definition '''

    def __init__(self):
        wsgi_app = tornado.wsgi.WSGIContainer(django.core.handlers.wsgi.WSGIHandler())
        handlers = [
            (r'/start_deploy/', Dhelper.DeployIt),
            (r'/get_running_jobs/', Dhelper.AnyJobsWeHave),
            (r'/listen/', Dhelper.GetLogHandler),
            ('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
        ]
        settings = dict()
        tornado.web.Application.__init__(self, handlers, default_host="", transforms=None, **settings)


def main():
    ''' Main loop of application '''

    parse_command_line()
    logging.info('Tornado Server starting...')
    app_log = tornado.log.app_log
    app_log.debug("Tornado run with next options: {}".format(options.as_dict()))
    signal.signal(signal.SIGINT, signal_handler)
    server = tornado.httpserver.HTTPServer(Application())
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
