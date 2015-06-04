''' Deployment Helper '''

import os
import concurrent.futures
import time
import logging
import tornado.websocket
import tornado.escape
import json
from functools import partial
import re

from deployerlib.config import Config
from deployerlib.commandline import CommandLine
from deployerlib.generatorhelper import GeneratorHelper
from deployerlib.executor import Executor
from deployerlib.exceptions import DeployerException
import deployerlib.log

# Django User access
from django.conf import settings
import django.contrib.auth
import django.utils.importlib

# Workaround to force threads exit because they are in infinity loop and crtl+c not work for Threads
# LISTENERS = {
#   'sessionid': {
#       'release': release ID string,
#       'socket': WebSocket Object
#       'buffer': [] List of lines before output to user
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

# TODO: before final merge any loop should be removed!
MAIN_RUN = True

# Get logger instance for Tornado
app_log = tornado.log.app_log


def run_deployment(data, timeout=5):
    args = None

    # dirty hack to cleanup log instances for deployer before start
    # in case it failed in the middle
    # TODO: rewrite to more elegant way
    deployerlib.log.set_is_web()
    deployerlib.log.clean_my_loggers()
    # Wait for 5 seconds, time required to client side successfully connected to socket after API call
    # TODO: need do this in more elegant way without unnecessary sleeps in thread
    #       As possible variant do not trigger deployment itself over Ajax API Call, but over socket API call
    #       After socket successfully connection established
    time.sleep(5)

    msg = "Release #{}: preparing for deployment.".format(data['release'])
    app_log.debug(msg)
    thread_to_wsockets(data['release'], format_to_json(data=msg))

    # Checking arguments in 'data' and build CommandLine parameters
    cmd_params = []
    cmd_params.append('--config')
    cmd_params.append(settings.DEPLOYER_CFGS + '/' + data['config_file'])
    if 'redeploy' in data.keys():
        cmd_params.append('--redeploy')
    cmd_params.append('--logdir')
    cmd_params.append(settings.LOG_DIR)
    args = CommandLine(command_line_args=cmd_params)

    msg = "Release #{}: complete build arguments for Deployment.\n".format(data['release'])
    app_log.debug(msg)
    thread_to_wsockets(data['release'], format_to_json(data=msg))

    config = Config(args)
    config.component = None
    config.release = None

    # Grab log file from args and pass it to our process information
    EXECPOOL[data['release']]['logfile'] = args.logfile
    msg = {'logfile': args.logfile, 'releaseid': data['release'], 'method': 'run_tail'}
    thread_to_wsockets(data['release'], format_to_json(calltype='api', data=msg))
    time.sleep(1)

    if 'components' in data and 'deployment_type' in data and data['deployment_type'] == 'component':
        config.component = []
        for component in data['components']:
            config.component.append(settings.DEPLOYER_TARS + '/' + data['release'] + '/' + component)
    elif 'deployment_type' in data and data['deployment_type'] == 'full':
        # Forced to use encode to UTF otherwise it throw critical error and exit
        config.release = [(settings.DEPLOYER_TARS + '/' + data['release'] + '/').encode('utf-8')]
    else:
        msg = "Release #{}: Looks like we got from you wrong parameters set and we unable build correct arguments for Deployer\n".format(data['release'])
        thread_to_wsockets(data['release'], format_to_json(data=msg))
        return False

    msg = "Release #{}: complete build configuration for Deployment.\n".format(data['release'])
    thread_to_wsockets(data['release'], format_to_json(data=msg))

    config.tasklist = None
    tasklist_builder = None

    msg = "Release #{}: building tasks list for Deployment.\n".format(data['release'])
    thread_to_wsockets(data['release'], format_to_json(data=msg))
    tasklist_builder = GeneratorHelper(config, config.platform)
    executor = Executor(tasklist=tasklist_builder.tasklist)
    if not settings.ENV_DEV:
        msg = "Release #{}: starting Deployment.\n".format(data['release'])
        thread_to_wsockets(data['release'], format_to_json(data=msg))
        executor.run()

    # Deployer Log instances cleanup after successful deployment
    deployerlib.log.clean_my_loggers()

    return "Index {} Return: Oops, i did it again :)".format(data['release'])


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
            app_log.debug("SocketId {} closed.".format(sid))


def before_deploy():
    ''' Preparation before deployment '''


# with concurrent.futures.ProcessPoolExecutor() as executor:
def run_thread(data):
    if len(EXECPOOL) < 1:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        th_data = {
            data['release']: {
                'process': executor.submit(run_deployment, data),
                'logfile': None
            }
        }
        EXECPOOL.update(th_data)
        return True
    else:
        return False


def check_process_alive():
    # for index, phandler in EXECPOOL.iteritems():
    for index in EXECPOOL.keys():
        app_log.debug("Process #{} finished its execution: {}".format(index, EXECPOOL[index]['process'].done()))
        if EXECPOOL[index]['process'].done() is True:
            app_log.debug("Process #{} removed from execution pool.".format(index))
            if EXECPOOL[index]['process'].exception(1):
                app_log.debug("Process #{} return Exception: {}".format(index, EXECPOOL[index]['process'].exception(1)))
            else:
                app_log.debug("Process #{} return: {}".format(index, EXECPOOL[index]['process'].result(1)))
            del EXECPOOL[index]


# Just for debug and learning
def print_variables():
    # print "WebSockets:"
    for x in LISTENERS:
        app_log.debug("Socket {}: {}/{}/{}".format(x, LISTENERS[x]['release'], len(LISTENERS[x]['buffer']), LISTENERS[x]['socket']))
    # print "Threads: "
    for y in EXECPOOL:
        app_log.debug("Thread {}: {}/{}".format(y, EXECPOOL[y]['process'], EXECPOOL[y]['logfile']))
    check_process_alive()

# Print to console each 5 seconds Listeners and Thread stats
prnt_vars = tornado.ioloop.PeriodicCallback(print_variables, 1000)
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


class AnyJobsWeHave(tornado.web.RequestHandler):
    ''' Return Json object of currently running jobs '''

    def post(self):
        user = get_django_user(self.get_cookie('sessionid', default=None))
        ugroups = user.groups.all().values_list('name', flat=True)

        payload = {}
        if not user.is_authenticated():
            msg = "You should pass authorization first!"
            payload.update(success=False, msg=msg)
            self.write(json.dumps(payload, default=None))
        else:
            plist = {}
            for process in EXECPOOL.keys():
                if any(x in process for x in ugroups):
                    plist[process] = {}
                    plist[process]['logfile'] = EXECPOOL[process]['logfile']
            payload.update(success=True, data={'jobs': plist, 'method': 'print_jobs'}, type='api')
            self.write(json.dumps(payload, default=None))

        self.set_header('Content-Type', 'application/json; charset=UTF-8')


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
            if self.runthread():
                payload.update(type='api', success=True)
                payload.update({'data': {'release': self.data['release']}})
                self.write(json.dumps(payload, default=None))
            else:
                msg = "Other Deployment in progress, visit deployment status page for details."
                payload.update(type='text', success=False, data=msg)
                self.write(json.dumps(payload, default=None))

        self.set_header('Content-Type', 'application/json; charset=UTF-8')

    def runthread(self):
        ''' call globally defined function run_thread() '''
        return run_thread(self.data)


# Example of Tail handler
class GetLogHandler(tornado.websocket.WebSocketHandler):
    def open(self, *args):

        self.csrftoken = self.get_cookie('csrftoken', default=None)
        self.sessionid = self.get_cookie('sessionid', default=None)
        self.index = self.get_argument("release", default=None)

        app_log.debug("WebSocket id {} opened".format(self.sessionid))

        if self.index:
            if self.sessionid in LISTENERS:
                LISTENERS[self.sessionid].update(release=self.index, socket=self, buffer=[])
            else:
                LISTENERS.update({self.sessionid: {'release': self.index, 'socket': self, 'buffer': []}})
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
        app_log.debug("WebSocket id {} closed!".format(self.sessionid))
        if LISTENERS[self.sessionid]:
            del LISTENERS[self.sessionid]
            try:
                self.tailed_callback
            except:
                ("Unable stop fucking LOOP! :D")  # need to remove
                pass
            else:
                self.tailed_callback.stop()

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
        self.tailed_callback = tornado.ioloop.PeriodicCallback(partial(self.check_file_buffered, tailed_file, self.sessionid, self.index), 1)
        self.tailed_callback.start()

    def open_file(self, logfile):
        ''' Open file which we want tail, file location in dict(data) '''
        try:
            tailed_file = open(logfile)
        except (OSError, IOError) as e:
            app_log.debug("Unable open log file {} with error {}".format(logfile, e))
            self.tailed_callback.stop()

        app_log.debug("Tail Descriptor: {}".format(tailed_file))
        tailed_file.seek(os.path.getsize(logfile))

        return tailed_file

    def check_file(self, tailed_file, sid):
        ''' Get Data from file and post it to Socket Stream '''
        where = tailed_file.tell()
        line = tailed_file.readline()
        if not line:
            tailed_file.seek(where)
        else:
            if sid in LISTENERS:
                try:
                    LISTENERS[sid]['socket'].write_message(format_to_json(data=line))
                except tornado.websocket.WebSocketClosedError:
                    app_log.debug("Socket {} with SocketId {} closed.".format(sid, LISTENERS[sid]['socket']))

    def check_file_buffered(self, tailed_file, sid, index):
        ''' Get Data from file and post it to Socket Stream '''

        # check if process still exist and running if not then we set flag to True, default flag False
        if (index not in EXECPOOL or EXECPOOL[index]['process'].done() is True) and len(LISTENERS[sid]['buffer']) > 0:
            # LISTENERS[sid]['buffer'].append("<span style=\"background-color: #00D627;\">Release #{}: Deployment process finished.</span>".format(index))
            self.send_buffer_socket(sid, LISTENERS[sid]['buffer'])
            # Close socket since thread done and we printed last amount of data to user
            # self.close(code=200, reason="Deployment job done all log entries printed. Socket Closed.")

        where = tailed_file.tell()
        line = tailed_file.readline()
        if not line:
            tailed_file.seek(where)
        else:
            if sid in LISTENERS:
                fline = self.output_filter(line)
                if fline:
                    LISTENERS[sid]['buffer'].append(fline)
                if len(LISTENERS[sid]['buffer']) > settings.WS_BUFFER_SIZE:
                    self.send_buffer_socket(sid, LISTENERS[sid]['buffer'])

    def output_filter(self, line):
        ''' Some kind of decoration for output before save it to buffer and return to user browser'''

        # Replace \n with nothing
        line = line.replace('\n', '')
        # Remove ANSI escape sequences
        ansi_escape = re.compile(r'\x1b[^m]*m')
        line = ansi_escape.sub('', line)

        # DEBUG Lines hidden
        if not tornado.options.options.debug and '[DEBUG' in line:
            return False

        # Warning/Critical and other type of colored decoration
        levels = {
            'got statuscode 200': '<span style="background-color: #00D627;">{}</span>',
            '[WARNING ]': '<span style="background-color: #ABACFF; font-weight:bold">{}</span>',
            '[ERROR ]': '<span style="background-color: magenta; font-weight:bold">{}</span>',
            '[CRITICAL ]': '<span style="background-color: red; font-weight:bold">{}</span>'
        }

        for x in levels.keys():
            if x in line:
                line = levels[x].format(line)

        # Add background color to Time output to do more readable lines of logs
        color_template = '<span style="background-color: #CCCCCC;">{}</span>'
        strdate = re.match('(\d{4})[/.-](\d{2})[/.-](\d{2}) (\d{2})[:](\d{2})[:](\d{2})[,](\d{3})', line)
        if strdate:
            tmpline = color_template.format(strdate.group())
            line = line.replace(strdate.group(), tmpline)

        return line

    def send_buffer_socket(self, sid, logbuffer):
        ''' Send log buffer to user socket, functionality written as method for more simple reuse '''
        try:
            LISTENERS[sid]['socket'].write_message(format_to_json(data="<br />".join(logbuffer)))
        except tornado.websocket.WebSocketClosedError:
            app_log.debug("Socket {} with SocketId {} closed.".format(sid, LISTENERS[sid]['socket']))
        else:
            LISTENERS[sid]['buffer'] = []
