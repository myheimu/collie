import logging
from django.shortcuts import render_to_response
from django import template
from django.contrib.auth.decorators import login_required

logger = logging.getLogger("collie")


@login_required
def index(request):
    return render_to_response('project_index.html', template.RequestContext(request))
