''' Django Views '''

import os
import yaml
import json
import re

from django.shortcuts import render_to_response, redirect
from django.http import HttpResponse
from django.template import RequestContext
# from loggers import get_logger
# import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user
from django.conf import settings
from django_auth_ldap.backend import LDAPBackend

# We will use Tornado Application Logging while Django coupled with Tornado
# app_log.info|critical|error|debug(MESSAGE)
from tornado.log import app_log

# logger = logging.getLogger('view_logger')


def niceName(release):
    groups = re.match(r'^([a-z/]+)-([0-9]{4})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})$', release)
    if groups:
        # return "%s %s-%s-%s %s:%s:%s" % groups.group(1,2,3,4,5,6,7)
        return "%s %s-%s-%s %s:%s:%s" % groups.groups()
    else:
        return None


def login_page(request, document_root=None):
    ''' Login page '''

    request_context = RequestContext(request)
    if request.user.is_authenticated():
        return redirect(settings.LOGIN_REDIRECT_URL)

    return render_to_response('auth.html', context_instance=request_context)


def authorize(request):
    ''' Where real authorization done '''

    request_context = RequestContext(request)

    user = authenticate(username=request.POST.get('username', None), password=request.POST.get('password', None))
    if user is not None:
        if user.is_active:
            login(request, user)
            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            return redirect(settings.LOGIN_URL)
    else:
        return redirect(settings.LOGIN_URL)


@login_required(redirect_field_name=None)
def logout_page(request):
    ''' Logout functionality '''

    request_context = RequestContext(request)
    logout(request)
    return redirect('/')


@login_required(redirect_field_name=None)
def list_configs(request):
    ''' Primary page after user successfully authorized '''

    request_context = RequestContext(request)
    # Example to how get some data about user by request dispatch
    # user.groups return django.db.models.query.QuerySet:
    # https://docs.djangoproject.com/en/1.8/ref/models/querysets/#values-list
    user = get_user(request)
    ugroups = user.groups.all().values_list('name', flat=True)
    tmp_configs = [x for x in os.listdir(settings.DEPLOYER_CFGS) if x.endswith('yaml') or x.endswith('conf')]
    configs = []
    for cfg in tmp_configs:
        if any(x in cfg for x in ugroups):
            configs.append(cfg)

    return render_to_response('list_configs.html', {'configs': configs}, context_instance=request_context)


@login_required(redirect_field_name=None)
def list_dirs(request):
    ''' List releases for specific configuration '''

    request_context = RequestContext(request)
    if request.method == 'POST':
        config = request.POST.get('config', None)
        if not config:
            # return HttpResponse('No such config exists')
            return redirect(settings.LOGIN_REDIRECT_URL)

        request.session['config_file'] = config
        try:
            fconf = open(settings.DEPLOYER_CFGS + '/{}'.format(config), 'r')
        except (OSError, IOError) as e:
            return HttpResponse('During file open next error returned: [{}]{}'.format(e.errno, e.strerror))
        else:
            try:
                cfg = yaml.load(fconf)
            except yaml.YAMLError, exc:
                return HttpResponse('We unable load yaml file due exception: {}'.format(exc))
            else:
                platform = cfg['platform'].replace('lp', '')
                # Static platform override, because native platform for static is aurora,
                # but packages hosted separately :(
                if 'static' in config:
                    platform = 'static'
                request.session['platform'] = platform
                request.session['tarballs'] = settings.DEPLOYER_TARS

    elif not request.session['platform'] or not request.session['tarballs']:
        return redirect(settings.LOGIN_REDIRECT_URL)

    releases = []
    for x in os.walk(request.session['tarballs']):
        if request.session['platform'] in x[0]:
            releaseId = x[0].replace('{}'.format(request.session['tarballs']), '')
            if niceName(releaseId):
                releases.append({'id': releaseId, 'niceName': niceName(releaseId)})

    releases = sorted(releases, key=lambda k: k['id'], reverse=True)

    return render_to_response('list_dirs.html', {'releases': releases}, context_instance=request_context)


@login_required(redirect_field_name=None)
def list_dir_content(request):
    ''' List directory content to allow component(s) selection '''

    request_context = RequestContext(request)
    if request.method == 'POST':
        release = request.POST.get('release', None)
        if not release:
            return list_dirs(request)
        else:
            request.session['release'] = release

    elif not request.session['platform'] or not request.session['tarballs']:
        return redirect(settings.LOGIN_REDIRECT_URL)

    files = [f for f in os.listdir(request.session['tarballs'] + '{}'.format(request.session['release']))]

    return render_to_response('list_dir_contents.html', {'components': files, 'release': request.session['release']}, context_instance=request_context)


@login_required(redirect_field_name=None)
def deploy_it(request):
    ''' Deployment actions which open connection to Websocket and pass into it required data '''

    request_context = RequestContext(request)
    if not request.session['platform'] or not request.session['tarballs']:
        return redirect(settings.LOGIN_REDIRECT_URL)
    if 'POST' not in request.method:
        return list_dir_content(request)

    params = {}

    if request.POST.get('release', None):
        request.session['release'] = request.POST.get('release', None)
    else:
        return list_dirs(request)

    # if user group not met condition then redirect user to home page
    user = get_user(request)
    ugroups = user.groups.all().values_list('name', flat=True)
    granted = False
    for x in ugroups:
        if x in request.session['release']:
            granted = True

    if not granted:
        return redirect(settings.LOGIN_REDIRECT_URL)

    components = request.POST.getlist('components', None)
    if request.POST.get('deployment_type', None) == 'component' and (type(components) is list and len(components) > 0):
        params.update(components=components, deployment_type=request.POST.get('deployment_type'))

    if request.POST.get('deployment_type', None) == 'full':
        params.update(deployment_type=request.POST.get('deployment_type'))

    if not request.session['platform'] or not request.session['tarballs'] or not request.session['config_file']:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.POST.get('redeploy', None):
        params.update(redeploy=True)
    # Build parameters we want to pass into Tornado from deployment page
    params.update(config_file=request.session['config_file'], release=request.session['release'], tarballs=request.session['tarballs'])
    # return render_to_response('progress.html', {'log_file': log_file, 'self_host': self_host}, context_instance=request_context)
    return render_to_response('progress.html', {'data': json.dumps(params), 'host': request.META['HTTP_HOST']}, context_instance=request_context)


@login_required(redirect_field_name=None)
def deploys_status(request):
    ''' Render page with currently ongoing deployments '''

    request_context = RequestContext(request)

    params = {}
    return render_to_response('deploys_status.html', {'data': json.dumps(params)}, context_instance=request_context)


@login_required(redirect_field_name=None)
def get_log(request):
    ''' Get deployment log during deployment '''

    request_context = RequestContext(request)
    payload = {}
    releaseid = request.POST.get('release', None)
    request.session['release'] = releaseid
    logfile = request.POST.get('logfile', None)

    if 'POST' not in request.method or not releaseid or not logfile:
        return deploys_status(request)

    payload.update(data={'releaseid': releaseid, 'logfile': logfile, 'method': 'read_from_memory'}, type='api')

    return render_to_response('progress2.html', {'data': json.dumps(payload), 'host': request.META['HTTP_HOST'], 'release': releaseid}, context_instance=request_context)
