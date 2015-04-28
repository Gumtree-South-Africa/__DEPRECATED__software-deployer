''' Django Views '''

import os
import simplejson
from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse
from django.template import RequestContext
from loggers import get_logger
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.conf import settings

logger = get_logger('view_logger')


def login_page(request, document_root=None):
    ''' Login page '''

    request_context = RequestContext(request)
    return render_to_response('auth.html', context_instance=request_context)


def authorize(request):
    ''' Where real authorization done '''

    request_context = RequestContext(request)
    print request.POST
    print request.GET

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
    if request.method == 'GET':
        # configs = [x for x in os.listdir('/etc') if x.endswith('.yaml')]
        configs = [x for x in os.listdir('etc/') if x.endswith('')]
        return render_to_response('list_configs_new.html', {'configs': configs}, context_instance=request_context)
