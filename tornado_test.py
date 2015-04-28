#!/usr/bin/env python

__author__ = 'vlazarenko'

import os
import sys
path = os.path.abspath(os.path.dirname(__file__))
if path not in sys.path:
    sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "deployerweb.settings")
import django
django.setup()

import django.core.handlers.wsgi
from tornado.options import options
import logging
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.wsgi
import tornado.websocket

# Futures
import concurrent.futures
import signal
import time
import random

tornado.options.define('port', type=int, default=8081, help='server port number (default: 8080)')
tornado.options.define('debug', type=bool, default=True, help='run in debug mode with autoreload (default: True)')
tornado.options.options.log_file_prefix = (path + '/logs/tornado_server.log')
tornado.options.options.log_file_max_size = (20*2**10*2**10)
tornado.options.parse_command_line()

# Workaround to force threads exit because they are in infinity loop and crtl+c not work for Threads
MAIN_RUN = True
LISTENERS = {}
EXECPOOL = {}


def do_something(index=0, timeout=None):
    count = 0
    while MAIN_RUN:
        if timeout and int(count) > int(timeout):
            break
        time.sleep(1)
        data = "My Index/Count/Time: {} - {}/{} - {}".format(index, count, timeout, time.strftime("%c"))
        print data
        if index in LISTENERS:
            for sid in LISTENERS[index]:
                sid.write_message(data)
        count += 1
    if timeout:
        print "My index {} passed {} counts, so i exiting....".format(index, count)
    else:
        print "My index {} and i exiting....".format(index)
    return "Index {} Return: Blah".format(index)


def signal_handler(signum, frame):
    global MAIN_RUN
    logging.info('exiting...')
    MAIN_RUN = False
    tornado.ioloop.IOLoop.instance().stop()


# with concurrent.futures.ProcessPoolExecutor() as executor:
def run_thread(index, timeout):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    EXECPOOL.update({index: executor.submit(do_something, index, timeout)})


def check_process_alive():
    # for index, phandler in EXECPOOL.iteritems():
    for index in EXECPOOL.keys():
        print "Process #{} finished its execution: {}".format(index, EXECPOOL[index].done())
        if EXECPOOL[index].done() is True:
            print EXECPOOL[index].exception(1)
            del EXECPOOL[index]


# Just for debug and learning
def print_variables():
    print "WebSockets:", LISTENERS
    print "Threads: ", EXECPOOL
    check_process_alive()


prnt_vars = tornado.ioloop.PeriodicCallback(print_variables, 5000)
prnt_vars.start()


class StartHandler(tornado.web.RequestHandler):
    def get(self):
        index = self.get_argument('index', default=random.seed(999999))
        timeout = self.get_argument('time', default=10)
        if index in EXECPOOL and EXECPOOL[index].running() is True:
            self.write("Process #{} already exist and still running.\n".format(index))
        else:
            run_thread(index, timeout)
            self.write("Process #{} started with timeout of {} cycles.\n".format(index, timeout))


class StatHandler(tornado.web.RequestHandler):
    def get(self):
        for ftr in EXECPOOL:
            self.write("Future: {}".format(ftr.running()))


class StopHandler(tornado.web.RequestHandler):
    def get(self):
        for ftr in EXECPOOL:
            self.write("Future: {}".format(ftr.running()))


class Md2kHandler(tornado.websocket.WebSocketHandler):
    def open(self, *args):
        print "WebSocket open"
        print self.get_cookie('csrftoken', default=None)
        print self.get_cookie('sessionid', default=None)
        self.index = self.get_argument("index", default=None)
        if self.index:
            if self.index in LISTENERS:
                LISTENERS[self.index].append(self)
            else:
                LISTENERS.update({self.index: [self]})

    def on_message(self, message):
        print 'message: ', message
        self.write_message(u"You successfully connected to socket and trying to listen from Sub-process index #{}".format(self.index))
        pass

    def on_close(self, *args):
        print "WebSocket close"
        try:
            if len(LISTENERS[self.index]) <= 1:
                del LISTENERS[self.index]
            else:
                LISTENERS[self.index].remove(self)
        except:
            pass


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
            (r'/stat/', StatHandler),
            (r'/start/', StartHandler),
            (r'/stop/', StopHandler),
            (r'/listen/', Md2kHandler),
            # (r'/progress/', MainHandler),
            ('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
        ]
        settings = dict()
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    logger = logging.getLogger(__name__)
    logger.info("Tornado server starting...")
    signal.signal(signal.SIGINT, signal_handler)
    server = tornado.httpserver.HTTPServer(Application())
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
