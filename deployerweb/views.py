# Create your views here.
import os

from django.shortcuts import render_to_response
from django.template import RequestContext
from loggers import get_logger

logger = get_logger('view_logger')

def list_releases(request):
    request_context = RequestContext(request)

    if request.method == 'GET':
        releases = [x[0] for x in os.walk('/opt/tarballs')]
        logger.debug(releases)
        return render_to_response('list_releases.html', {'data': releases}, context_instance=request_context)
