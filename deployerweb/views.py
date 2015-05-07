''' Django Views '''

import os
import simplejson
import yaml
import json

from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse
from django.template import RequestContext
from loggers import get_logger
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user
from django.conf import settings

logger = get_logger('view_logger')


def login_page(request, document_root=None):
    ''' Login page '''

    request_context = RequestContext(request)
    if request.user.is_authenticated():
        return redirect(settings.LOGIN_REDIRECT_URL)

    return render_to_response('auth.html', context_instance=request_context)


def authorize(request):
    ''' Where real authorization done '''

    request_context = RequestContext(request)
    # print request.POST
    # print request.GET

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
    print user.groups.all().values_list('name', flat=True)
    # print user.groups.all()[0]
    # print user.get_group_permissions()
    # print user.user_permissions.all()
    # if user.groups.filter(name='icas').exists():
    #    print "in group icas"
    # user.groups.filter(name__in=['group1', 'group2']).exists()

    # if request.method == 'GET':
    # configs = [x for x in os.listdir('/etc') if x.endswith('.yaml')]
    configs = [x for x in os.listdir(settings.DEPLOYER_CFGS) if x.endswith('')]
    return render_to_response('list_configs_new.html', {'configs': configs}, context_instance=request_context)


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
                request.session['platform'] = cfg['platform'].replace('lp', '')
                request.session['tarballs'] = settings.DEPLOYER_TARS

    elif not request.session['platform'] or not request.session['tarballs']:
        return redirect(settings.LOGIN_REDIRECT_URL)

    dirs = sorted([x[0].replace('{}'.format(request.session['tarballs']), '') for x in os.walk(request.session['tarballs']) if request.session['platform'] in x[0]])
    print dirs
    return render_to_response('list_dirs_new.html', {'releases': dirs}, context_instance=request_context)


@login_required(redirect_field_name=None)
def list_dir_content(request):
    ''' List directory content to allow component(s) selection '''

    request_context = RequestContext(request)
    if request.method == 'POST':
        release = request.POST.get('release', None)
        if not release:
            return list_dirs(request)

        request.session['release'] = release

    elif not request.session['platform'] or not request.session['tarballs']:
        return redirect(settings.LOGIN_REDIRECT_URL)

    files = [f for f in os.listdir(request.session['tarballs'] + '{}'.format(request.session['release']))]

    return render_to_response('list_dir_contents_new.html', {'components': files, 'release': request.session['release']}, context_instance=request_context)


@login_required(redirect_field_name=None)
def deploy_it(request):
    ''' Deployment actions which open connection to Websocket and pass into it required data '''

    request_context = RequestContext(request)
    if not request.session['platform'] or not request.session['tarballs']:
        return redirect(settings.LOGIN_REDIRECT_URL)
    if 'POST' not in request.method:
        return list_dir_content(request)

    params = {}

    components = request.POST.getlist('components', None)
    request.session['release'] = request.POST.get('release', None)
    if request.POST.get('deployment_type', None) == 'component' and (type(components) is list and len(components) > 0):
        # print len(components)
        # print request.POST.getlist('components', None)
        params.update(components=components, deployment_type=request.POST.get('deployment_type'))

    if request.POST.get('deployment_type', None) == 'full':
        params.update(deployment_type=request.POST.get('deployment_type'))

    if not request.session['platform'] or not request.session['tarballs'] or not request.session['config_file']:
        return redirect(settings.LOGIN_REDIRECT_URL)

    # Build parameters we want to pass into Tornado from deployment page
    params.update(config_file=request.session['config_file'], release=request.session['release'], tarballs=request.session['tarballs'])
    # print json.dumps(params)
    # return render_to_response('progress.html', {'log_file': log_file, 'self_host': self_host}, context_instance=request_context)
    return render_to_response('progress_new.html', {'data': json.dumps(params), 'host': request.META['HTTP_HOST']}, context_instance=request_context)


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
    params = {}
    payload = {}
    releaseid = request.POST.get('release', None)
    logfile = request.POST.get('logfile', None)

    if 'POST' not in request.method or not releaseid or not logfile:
        return deploys_status(request)

    payload.update(data={'releaseid': releaseid, 'logfile': logfile, 'method': 'run_tail'}, type='api')

    return render_to_response('progress_new2.html', {'data': json.dumps(payload), 'host': request.META['HTTP_HOST'], 'release': releaseid}, context_instance=request_context)
