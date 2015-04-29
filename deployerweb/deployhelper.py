import os
import sys
import concurrent.futures
import time
import random
import logging
import tornado.websocket

import argparse
from loggers import get_logger

from attrdict import AttrDict

from deployerlib.config import Config
from deployerlib.commandline import CommandLine
from deployerlib.tasklist import Tasklist
from deployerlib.executor import Executor
from deployerlib.exceptions import DeployerException

# Workaround to force threads exit because they are in infinity loop and crtl+c not work for Threads
LISTENERS = {}
EXECPOOL = {}
MAIN_RUN = True


def do_something(index=0, timeout=None):
    count = 0
    args = None
    while MAIN_RUN:
        if timeout and int(count) > int(timeout):
            break
        time.sleep(1)
        data = "My Index/Count/Time: {} - {}/{} - {}".format(index, count, timeout, time.strftime("%c"))

        if not args:
            args = CommandLine(command_line_args=['--config', '/Users/yflerko/git/eBay/web2_deployer/mp-conf/platform-aurora.yaml', '--redeploy', '--logdir', '/Users/yflerko/git/eBay/web2_deployer/logs'])
            print args
            #config = Config(args)
            #config.component = None
            #config.release = ['/Users/yflerko/git/eBay/web2_deployer/mp-tars/aurora-20150422152017']
            #config.tasklist = None
            #tasklist_builder = None
            #tasklist_builder = Tasklist(config, config.platform)
            #Executor(tasklist=tasklist_builder.tasklist)
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
            # print EXECPOOL[index].result(1)
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
