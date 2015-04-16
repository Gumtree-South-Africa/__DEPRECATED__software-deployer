# Create your views here.
import os
from os import listdir

import argparse

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from loggers import get_logger

from attrdict import AttrDict

from deployerlib.config import Config
from deployerlib.commandline import CommandLine
from deployerlib.tasklist import Tasklist
from deployerlib.executor import Executor
from deployerlib.exceptions import DeployerException

logger = get_logger('view_logger')

def list_configs(request):
    request_context = RequestContext(request)
    if request.method == 'GET':
        configs = [x for x in listdir('/etc/marktplaats') if x.endswith('.yaml')]
        return render_to_response('list_configs.html', {'configs': configs}, context_instance=request_context)

def list_dirs(request):
    request_context = RequestContext(request)

    if request.method == 'POST':
        config = request.POST.get('config_file', None)
        if not config:
            return HttpResponse('No such config exists')

        request.session['config_file'] = config
        args = CommandLine(command_line=['--config', '/etc/marktplaats/{}'.format(config)])
        config = Config(args)
        logger.debug(config.tarballs)
        platform = config.platform.replace('lp', '')
        dirs = sorted([x[0].replace('{}/'.format(config.tarballs), '') for x in os.walk(config.tarballs) if platform in x[0]])
        return render_to_response('list_dirs.html', {'data': dirs}, context_instance=request_context)


def list_dir_contents(request, directory):

    request_context = RequestContext(request)
    if request.method == 'GET':
        if not directory:
            return list_dirs(request)


    files = [ f for f in listdir('/opt/tarballs/{}'.format(directory)) ]
    logger.debug(files)
    return render_to_response('list_dir_contents.html', {'data': files, 'directory': directory}, context_instance=request_context)


def deploy_release(request):
    request_context = RequestContext(request)
    config_file = request.session.get('config_file')
    logger.debug(request.POST)

    if not config_file:
        return HttpResponse('No config defined, oops')

    if request.POST.get('redeploy'):
        args = CommandLine(command_line=['--config', '/etc/marktplaats/{}'.format(config_file), '--redeploy'])
    else:
        args = CommandLine(command_line=['--config', '/etc/marktplaats/{}'.format(config_file), '--redeploy'])

    config = Config(args)
    config.component = None
    config.release = [ '{}/{}'.format(config.tarballs, request.POST.get('release_to_deploy')) ]
    config.tasklist = None

    tasklist_builder = None

    try:
        tasklist_builder = Tasklist(config, config.platform)
    except DeployerException as e:
        logger.critical('Failed to generate task list: {0}.'.format(e))

    if not tasklist_builder:
        return HttpResponse('Could not generate tasklist. I can take you <a href="/">home</a> instead')

    if not tasklist_builder.tasklist:
        return HttpResponse('You\'re all set, there is nothing to deploy. I can take you <a href="/">home</a> instead')

    executor = Executor(tasklist=tasklist_builder.tasklist)
    #executor.run()


    return HttpResponse('Hey, I\'ve rendered all I could, now go <a href="/">home</a>')

def deploy_component(request):
    request_context = RequestContext(request)
    config_file = request.session.get('config_file')
    logger.debug(request.POST)

    if not config_file:
        return HttpResponse('No config defined, oops')

    if request.POST.get('redeploy'):
        args = CommandLine(command_line=['--config', '/etc/marktplaats/{}'.format(config_file), '--redeploy'])
    else:
        args = CommandLine(command_line=['--config', '/etc/marktplaats/{}'.format(config_file), '--redeploy'])

    config = Config(args)
    config.release = None
    config.component = [ '{}/{}/{}'.format(config.tarballs, request.POST.get('directory'), request.POST.get('component_to_deploy')) ]
    config.tasklist = None

    tasklist_builder = None

    try:
        tasklist_builder = Tasklist(config, config.platform)
    except DeployerException as e:
        logger.critical('Failed to generate task list: {0}.'.format(e))


    if not tasklist_builder:
        return HttpResponse('Could not generate tasklist. I can take you <a href="/">home</a> instead')

    if not tasklist_builder.tasklist:
        return HttpResponse('You\'re all set, there is nothing to deploy. I can take you <a href="/">home</a> instead')

    executor = Executor(tasklist=tasklist_builder.tasklist)
    #executor.run()


    return HttpResponse('Hey, I\'ve rendered all I could, now go <a href="/">home</a>')

