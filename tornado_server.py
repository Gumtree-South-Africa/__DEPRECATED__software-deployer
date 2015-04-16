#!/usr/bin/env python

__author__ = 'vlazarenko'

import os
import sys
path = os.path.abspath(os.path.dirname(__file__))
if path not in sys.path:
    sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "deployerweb.settings")
from tornado.options import options
import django.core.handlers.wsgi
import logging
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.wsgi
import tornado.websocket

tornado.options.define('port', type=int, default=8080, help='server port number (default: 8080)')
tornado.options.define('debug', type=bool, default=True, help='run in debug mode with autoreload (default: True)')
tornado.options.options['log_file_prefix'].set(path + '/logs/tornado_server.log')
tornado.options.options['log_file_max_size'].set(20*2**10*2**10)
tornado.options.parse_command_line()

LISTENERS = []

def check_file():
    where = tailed_file.tell()
    line = tailed_file.readline()
    if not line:
        tailed_file.seek(where)
    else:
        print "File refresh"
        for element in LISTENERS:
            element.write_message(line)

class TailHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print "WebSocket open"
        LISTENERS.append(self)

    def on_message(self, message):
        pass

    def on_close(self):
        print "WebSocket close"
        try:
            LISTENERS.remove(self)
        except:
            pass

class Application(tornado.web.Application):
    def __init__(self):
        wsgi_app = tornado.wsgi.WSGIContainer(django.core.handlers.wsgi.WSGIHandler())
        handlers = [
            (r'/tail/', TailHandler),
            ('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
        ]
        settings = dict()
        tornado.web.Application.__init__(self, handlers, **settings)

def main():
    logger = logging.getLogger(__name__)
    logger.info("Tornado server starting...")
    server = tornado.httpserver.HTTPServer(Application())
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
