#!/usr/bin/env python2.7

__author__ = 'vlazarenko and yflerko'

import os

# Run this with
# PYTHONPATH=. DJANGO_SETTINGS_MODULE=testsite.settings testsite/tornado_main.py
# Below code to allow us skip action above:
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "deployerweb.settings")

from tornado.options import options, define, parse_command_line
import django.core.handlers.wsgi
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.wsgi
import tornado.websocket
import logging
import signal
import deployerweb.deployhelper as Dhelper
from django.conf import settings

# Bypassing manage.py starts from Django 1.6 and newer
# https://docs.djangoproject.com/en/1.8/intro/tutorial01/#playing-with-the-api
if django.VERSION[1] > 5:
    django.setup()

# Tornado options, need find better place for them later
# to Run it in debug mode use flag '--debug=True'
define('port', type=int, default=8080, help='server port number (default: 8080)')
define('debug', type=bool, default=False, help='run in debug mode with autoreload (default: True)')
options.log_file_prefix = (settings.LOG_DIR + '/tornado_server.log')
options.log_file_max_size = (20*2**10*2**10)


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
        setting = dict()
        tornado.web.Application.__init__(self, handlers, **setting)


def main():
    ''' Main loop of application '''

    setting = dict()
    parse_command_line()
    logging.info("Tornado server starting...")
    signal.signal(signal.SIGINT, signal_handler)
    server = tornado.httpserver.HTTPServer(Application(), **setting)
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
