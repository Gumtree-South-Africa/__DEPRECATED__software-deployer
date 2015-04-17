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
tornado.options.options.log_file_prefix = (path + '/logs/tornado_server.log')
tornado.options.options.log_file_max_size = (20*2**10*2**10)
tornado.options.parse_command_line()

LISTENERS = []


# def check_file(tailed_file):
#     where = tailed_file.tell()
#     line = tailed_file.readline()
#     if not line:
#         tailed_file.seek(where)
#     else:
#         print "File refresh"
#         for element in LISTENERS:
#             element.write_message(line)


class TailHandler(tornado.websocket.WebSocketHandler):
    def open(self, *args):
        print "WebSocket open"
        LISTENERS.append(self)
        self.log_file = self.get_argument("file")
        self.open_file()
        self.tailed_callback = tornado.ioloop.PeriodicCallback(self.check_file, 100)
        self.tailed_callback.start()

    def on_message(self, message):
        print 'message: ', message
        self.write_message(u"You successfully connected to socket and requested tail for flie: {}".format(self.log_file))
        pass

    def on_close(self, *args):
        print "WebSocket close"
        self.tailed_callback.stop()
        self.tailed_file.close()
        try:
            LISTENERS.remove(self)
        except:
            pass

    def open_file(self):
        tailed_file = open(path + "/" + self.log_file)
        print tailed_file
        tailed_file.seek(os.path.getsize(path + "/" + self.log_file))
        self.tailed_file = tailed_file

    def check_file(self):
        where = self.tailed_file.tell()
        line = self.tailed_file.readline()
        if not line:
            self.tailed_file.seek(where)
        else:
            print "File refresh"
            for element in LISTENERS:
                element.write_message(line)


class Application(tornado.web.Application):
    def __init__(self):
        wsgi_app = tornado.wsgi.WSGIContainer(django.core.handlers.wsgi.WSGIHandler())
        handlers = [
            (r'/tail/', TailHandler),
            # (r'/progress/', MainHandler),
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
