import os
import sys
import concurrent.futures
import time
import random
import logging
import tornado.websocket
import tornado.escape
import json
from functools import partial

import argparse
from loggers import get_logger

from attrdict import AttrDict

from deployerlib.config import Config
from deployerlib.commandline import CommandLine
from deployerlib.tasklist import Tasklist
from deployerlib.executor import Executor
from deployerlib.exceptions import DeployerException
import deployerlib.log

import inspect

# Django User access
from django.conf import settings
import django.contrib.auth
import django.utils.importlib

# Workaround to force threads exit because they are in infinity loop and crtl+c not work for Threads
# LISTENERS = {
#   'sessionid': {
#       'release': release ID string,
#       'socket': WebSocket Object
#   }
# }
LISTENERS = {}
# EXECPOOL = {
#   releaseid: {
#       'process': Future Object,
#       'logfile': Full Log Path as String
#   }
# }
EXECPOOL = {}
MAIN_RUN = True


def run_deployment(data, timeout=5):
    count = 0
    args = None
    while MAIN_RUN:
        if timeout and int(count) > int(timeout):
            break
        time.sleep(1)
        msg = "My index {}: Current cycle {} / {}".format(data['release'], count, timeout)
        print msg
        thread_to_wsockets(data['release'], format_to_json(data=msg))

        if not args:
            print logging.Logger.manager.loggerDict

            msg = "My index {}: preparing for deployment.".format(data['release'])
            print msg
            thread_to_wsockets(data['release'], format_to_json(data=msg))

            # Checking arguments in 'data' and build CommandLine parameters
            cmd_params = []
            cmd_params.append('--config')
            cmd_params.append(settings.DEPLOYER_CFGS + '/' + data['config_file'])
            # if data['redeploy']:
            cmd_params.append('--redeploy')
            cmd_params.append('--logdir')
            cmd_params.append(settings.BASE_DIR + '/logs')
            args = CommandLine(command_line_args=cmd_params)

            msg = "We complete build arguments for Deployment.\n"
            thread_to_wsockets(data['release'], format_to_json(data=msg))

            config = Config(args)
            config.component = None
            config.release = None

            # Grab log file from args and pass it to our process information
            EXECPOOL[data['release']]['logfile'] = args.logfile
            # msg = json.dumps({'logfile': args.logfile, 'releaseid': data['release'], 'method': 'run_tail'})
            msg = {'logfile': args.logfile, 'releaseid': data['release'], 'method': 'run_tail'}
            thread_to_wsockets(data['release'], format_to_json(calltype='api', data=msg))

            if data['components'] and data['deployment_type'] == 'component':
                config.component = []
                for component in data['components']:
                    config.component.append(settings.DEPLOYER_TARS + '/' + data['release'] + '/' + component)
            elif data['deployment_type'] == 'full':
                config.release = [settings.DEPLOYER_TARS + '/' + data['release'] + '/']
            else:
                msg = "Looks like we got from you wrong parameters set and we unable build correct arguments for Deployer\n"
                thread_to_wsockets(data['release'], format_to_json(data=msg))
                break

            msg = "We complete build configuration for Deployment.\n"
            thread_to_wsockets(data['release'], format_to_json(data=msg))

            config.tasklist = None
            tasklist_builder = None
            tasklist_builder = Tasklist(config, config.platform)
            executor = Executor(tasklist=tasklist_builder.tasklist)
            # executor.run()

        count += 1
    if timeout:
        msg = "My index {} passed {} counts, so i exiting....".format(data['release'], count)
        print msg
        thread_to_wsockets(data['release'], format_to_json(data=msg))
    else:
        msg = "My index {} and i exiting....".format(data['release'])
        print msg
        thread_to_wsockets(data['release'], format_to_json(data=msg))

    # Destroy Deployment Loggers
    if deployerlib.log.LogDict:
        for logname in deployerlib.log.LogDict.keys():
            print "Destroying logger {}".format(logname)
            del logging.Logger.manager.loggerDict[logname]
            del deployerlib.log.LogDict[logname]
    print deployerlib.log.LogDict
    print logging.Logger.manager.loggerDict
    return "Index {} Return: Blah".format(data['release'])


def format_to_json(calltype='text', data=False):
    '''
        Json formatter for messages.
        Default calltype `text`, can be `api`
        text - just messages which should be posted to screen
        api  - data which should be treated as API calls between UI/Serverside
               Api calls can be UI related and Server side related.
        data - dict/json object with required data or simple message if calltype=text
               or hold some data sets required for execution on server side or UI side if API call
    '''
    if calltype == 'text':
        result = {'type': calltype, 'data': data}
    elif calltype == 'api':
        result = {'type': calltype, 'data': data}

    return result


def thread_to_wsockets(myid, message):
    '''
        Global function which is writes from thread to all opened WebSocets
        which is connected for specific deployment ID
        where is ID - release name for example 'aurora-20150422152017'
        WebSocket ID - session id of the user's session
    '''

    # Get all sockets where we want to write first
    wsockets = [LISTENERS[x]['socket'] for x in LISTENERS if myid in LISTENERS[x]['release']]

    for sid in wsockets:
        try:
            sid.write_message(message)
        except tornado.websocket.WebSocketClosedError:
            print "SocketId {} closed.".format(sid)


def before_deploy():
    ''' Preparation before deployment '''


# with concurrent.futures.ProcessPoolExecutor() as executor:
def run_thread(data):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    th_data = {
        data['release']: {
            'process': executor.submit(run_deployment, data),
            'logfile': None
        }
    }
    EXECPOOL.update(th_data)


def check_process_alive():
    # for index, phandler in EXECPOOL.iteritems():
    for index in EXECPOOL.keys():
        print "Process #{} finished its execution: {}".format(index, EXECPOOL[index]['process'].done())
        if EXECPOOL[index]['process'].done() is True:
            print EXECPOOL[index]['process'].exception(1)
            # print EXECPOOL[index].result(1)
            del EXECPOOL[index]


# Just for debug and learning
def print_variables():
    print "WebSockets:", LISTENERS
    print "Threads: ", EXECPOOL
    check_process_alive()


prnt_vars = tornado.ioloop.PeriodicCallback(print_variables, 5000)
prnt_vars.start()


def get_django_user(session_key):
    ''' Get user by its session from Django Session Storage
        Return UserModel or AnonymousUser if not found
    '''

    engine = django.utils.importlib.import_module(django.conf.settings.SESSION_ENGINE)
    request = DummyObject()
    request.session = engine.SessionStore(session_key)
    return django.contrib.auth.get_user(request)


class DummyObject:
    ''' we want have empty objects '''
    pass


class DeployIt(tornado.web.RequestHandler):
    ''' API Call to run deployment thread '''

    def post(self):
        user = get_django_user(self.get_cookie('sessionid', default=None))
        payload = {}
        data = tornado.escape.json_decode(self.request.body)
        if not data['deployit']:
            msg = "We not received properly formed Json data"
            payload.update(success=False, msg=msg)
            self.write(json.dumps(payload, default=None))

        elif not user.is_authenticated():
            msg = "You should pass authorization first!"
            payload.update(success=False, msg=msg)
            self.write(json.dumps(payload, default=None))

        else:
            self.data = data['deployit']
            self.runthread()
            payload.update(type='api', success=True)
            payload.update({'data': {'release': self.data['release']}})
            self.write(json.dumps(payload, default=None))

        self.set_header('Content-Type', 'application/json; charset=UTF-8')

    def runthread(self):
        ''' call globally defined function run_thread() '''
        run_thread(self.data)


# Example of Tail handler
class Md2kHandler(tornado.websocket.WebSocketHandler):
    def open(self, *args):
        print "WebSocket open"
        self.csrftoken = self.get_cookie('csrftoken', default=None)
        self.sessionid = self.get_cookie('sessionid', default=None)
        print self.csrftoken, self.sessionid
        self.index = self.get_argument("release", default=None)
        if self.index:
            if self.index in LISTENERS:
                LISTENERS[self.sessionid].update(release=self.index, socket=self)
            else:
                LISTENERS.update({self.sessionid: {'release': self.index, 'socket': self}})
            # Tell on success connection that we connected
            self.write_message(format_to_json(data=u"You successfully connected to socket and trying to listen from Sub-process index #{}".format(self.index)))

    def on_message(self, message):

        try:
            jsonmsg = json.loads(message.decode('utf8'))
        except ValueError:
            pass
        else:
            self.json_api_call(jsonmsg)

    def on_close(self):
        print "WebSocket close!!!!!"
        if LISTENERS[self.sessionid]:
            del LISTENERS[self.sessionid]
            try:
                self.tailed_callback
            except:
                pass
            else:
                self.tailed_callback.stop()
        print "Current opened Socket connections: ", LISTENERS

    def json_api_call(self, jdata):
        ''' processing of json received from socket '''
        if jdata['type'] == 'api':
            method_call = getattr(self, jdata['data']['method'])
            if method_call:
                method_call(jdata['data'])
            else:
                self.write_message(format_to_json(data=u"Requested method not found: {}".format(jdata['data']['method'])))

    def run_tail(self, data):
        ''' Prepare and run Tail as part of Tornado Event loop '''

        tailed_file = self.open_file(data['logfile'])
        self.tailed_callback = tornado.ioloop.PeriodicCallback(partial(self.check_file, tailed_file, self.sessionid), 1)
        self.tailed_callback.start()

    def open_file(self, logfile):
        ''' Open file which we want tail, file location in dict(data) '''
        try:
            tailed_file = open(logfile)
        except (OSError, IOError) as e:
            print "Unable open log file {} with error {}".format(logfile, e)
            self.tailed_callback.stop()

        print "Tail Descriptor: ", tailed_file
        tailed_file.seek(os.path.getsize(logfile))
        return tailed_file

    def check_file(self, tailed_file, sid):
        ''' Get Data from file and post it to Socket Stream '''
        where = tailed_file.tell()
        line = tailed_file.readline()
        if not line:
            tailed_file.seek(where)
        else:
            # print "File refresh"
            if sid in LISTENERS:
                try:
                    LISTENERS[sid]['socket'].write_message(format_to_json(data=line))
                except tornado.websocket.WebSocketClosedError:
                    print "Socket {} with SocketId {} closed.".format(sid, LISTENERS[sid]['socket'])
