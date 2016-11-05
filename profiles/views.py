# Create your views here.
import base64
import json
import logging
import os
from django import template
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from core.utils import get_uploaded_file_content
from profiles.models import KerberosKeys, GroupRequest, CollieGroup
from settings import settings


logger = logging.getLogger('collie')


@login_required()
def profile_index(request):
    username = request.user.username
    context = {
        'username': username
    }
    return render_to_response('profile/account.html', context, context_instance=RequestContext(request))


@login_required()
def profile_nickname(request):
    username = request.user.username
    context = {
        'status': 1,
        'user_info': {
            'nickname': username
        }
    }
    return HttpResponse(json.dumps(context), mimetype='application/json')


@login_required()
def profile_kerberos(request):
    username = request.user.username
    keys = []
    kerberos_keys = KerberosKeys.objects.filter(username=username)
    if not kerberos_keys is None:
        for kerberos_key in kerberos_keys:
            keys.append({
                'name': kerberos_key.name
            })
    context = {
        'keys': keys
    }
    return render_to_response('profile/kerberos.html', context, context_instance=RequestContext(request))


@login_required()
def profile_principal(request):
    username = request.user.username
    context = {

    }
    return render_to_response('profile/principal_user.html', context, context_instance=RequestContext(request))


@login_required()
@csrf_exempt
def profile_kerberos_upload(request):
    if request.method == 'POST':
        job_file = request.FILES['Filedata']
        file_path = job_file.name
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
        path = default_storage.save(job_file.name, ContentFile(job_file.read()))
        logger.info(path)

    res_json = dict()
    res_json["status"] = 1
    return HttpResponse(json.dumps(res_json), mimetype="application/json")


@login_required()
@csrf_exempt
def profile_kerberos_save(request):
    username = request.user.username
    name = request.POST.get('name')
    file = request.POST.get('file')

    # mv file
    source = settings.MEDIA_PATH + file
    if not os.path.isfile(source):
        context = {
            'status': -1,
            'error': 'please upload file first'
        }
        return HttpResponse(json.dumps(context), mimetype="application/json")

    # filter name conflict
    kerberos_keys = KerberosKeys.objects.filter(username=username, name=name)
    if not kerberos_keys is None and len(kerberos_keys) > 0:
        context = {
            'status': -1,
            'error': 'key name already existed'
        }
        return HttpResponse(json.dumps(context), mimetype="application/json")

    # save
    file_raw = get_uploaded_file_content(file)
    file_content = base64.b64encode("".join(file_raw))
    kerberos_key = KerberosKeys(name=name,
                                username=username,
                                file=file_content)
    kerberos_key.save()

    # delete unused temp file
    os.remove(source)

    context = {
        'status': 1
    }
    return HttpResponse(json.dumps(context), mimetype="application/json")


@login_required()
@csrf_exempt
def profile_kerberos_delete(request):
    username = request.user.username
    name = request.POST.get('name')

    # delete in db
    kerberos_key = KerberosKeys.objects.filter(username=username, name=name)[:1].get()
    kerberos_key.delete()

    context = {
        'status': 1
    }
    return HttpResponse(json.dumps(context), mimetype="application/json")


@login_required()
def profile_groups_page(request):
    username = request.user.username
    user = User.objects.get(username=username)
    groups = user.groups.all()
    res_groups = []
    requests = []
    for group in groups:
        collie_group = CollieGroup.objects.get(id=group.id)
        if collie_group.has_admin(username):
            res_groups.append({
                'name': group.name,
                'is_owner': True
            })
            requests.extend(get_requests(collie_group.name))
        else:
            res_groups.append({
                'name': group.name,
                'is_owner': False
            })
    context = {
        'groups': res_groups,
        'requests': requests
    }
    return render_to_response('profile/groups.html', context, template.RequestContext(request))


@login_required()
def verify_group_name(request):
    username = request.user.username
    group_name = request.GET.get('group_name')
    logger.debug('user %s verify group name %s', username, group_name)
    try:
        CollieGroup.objects.get(name=group_name)
        context = {
            'status': 1,
            'result': 'succeed: group existed'
        }
        logger.debug('group %s do exist', group_name)
        return HttpResponse(json.dumps(context), mimetype="application/json")
    except ObjectDoesNotExist:
        context = {
            'status': 1,
            'result': 'failed: no such group existed'
        }
        logger.debug('group %s does not exist', group_name)
        return HttpResponse(json.dumps(context), mimetype="application/json")


@login_required()
@csrf_exempt
def create_group(request):
    username = request.user.username
    group_name = request.POST.get('group_name')
    logger.info('user %s create group %s', username, group_name)

    collie_groups = CollieGroup.objects.filter(name=group_name)
    if len(collie_groups) > 0:
        context = {
            'status': -1,
            'error': 'duplicate group name found, please change another name'
        }
        logger.error('duplicate group name %s', group_name)
        return HttpResponse(json.dumps(context), mimetype='application/json')

    collie_group = CollieGroup(name=group_name,
                               admins=username)
    collie_group.save()

    # add user to group
    user = User.objects.get(username=username)
    collie_group.user_set.add(user)
    context = {
        'status': 1
    }
    logger.info('user create group succeed, res %s', context)
    return HttpResponse(json.dumps(context), mimetype="application/json")


@login_required()
@csrf_exempt
def join_group(request):
    username = request.user.username
    group_name = request.POST.get('group_name')
    logger.info('user %s want to join group %s', username, group_name)

    user = User.objects.get(username=username)
    group = Group.objects.get(name=group_name)

    group_requests = GroupRequest.objects.filter(user=user, group=group)
    if len(group_requests) > 0:
        context = {
            'status': 1
        }
        return HttpResponse(json.dumps(context), mimetype='application/json')
    group_request = GroupRequest(user=user,
                                 group=group)
    group_request.save()
    context = {
        'status': 1
    }
    logger.info('user has applied succeed, res %s', context)
    return HttpResponse(json.dumps(context), mimetype="application/json")


def get_requests(group_name):
    group = CollieGroup.objects.get(name=group_name)
    group_requests = GroupRequest.objects.filter(group=group)
    requests = []
    for group_request in group_requests:
        request_user = group_request.user
        request_group = group_request.group
        requests.append({
            'user_name': request_user.username,
            'group_name': request_group.name
        })
    return requests


@login_required()
@csrf_exempt
def approve_group(request):
    username = request.user.username
    group_name = request.POST.get('group_name')
    applicant_name = request.POST.get('applicant_name')
    logger.info('user %s approve %s to join group %s', username, applicant_name, group_name)

    group = CollieGroup.objects.get(name=group_name)
    applicant_user = User.objects.get(username=applicant_name)
    has_admin = group.has_admin(username)
    if not has_admin:
        context = {
            'status': -1,
            'error': 'you are not admin of this group ' + group_name
        }
        logger.error('approved failed, coz you %s are not admin of this group %s', username, group_name)
        return HttpResponse(json.dumps(context), mimetype="application/json")

    try:
        group_request = GroupRequest.objects.get(user=applicant_user,
                                                 group=group)
    except ObjectDoesNotExist:
        context = {
            'status': 1
        }
        logger.error('this approval has been handled')
        return HttpResponse(json.dumps(context), mimetype="application/json")

    group.user_set.add(applicant_user)
    group_request.delete()
    context = {
        'status': 1
    }
    logger.info('user %s has joined group %s by admin %s', applicant_name, group_name, username)
    return HttpResponse(json.dumps(context), mimetype="application/json")


@login_required()
@csrf_exempt
def deny_group(request):
    username = request.user.username
    group_name = request.POST.get('group_name')
    applicant_name = request.POST.get('applicant_name')
    logger.info('user %s deny %s to join group %s', username, applicant_name, group_name)

    group = CollieGroup.objects.get(name=group_name)
    applicant_user = User.objects.get(username=applicant_name)
    has_admin = group.has_admin(username)
    if not has_admin:
        context = {
            'status': -1,
            'error': 'you are not admin of this group ' + group_name
        }
        logger.error('deny failed, coz you %s are not admin of this group %s', username, group_name)
        return HttpResponse(json.dumps(context), mimetype="application/json")

    try:
        group_request = GroupRequest.objects.get(user=applicant_user,
                                                 group=group)
    except ObjectDoesNotExist:
        context = {
            'status': 1
        }
        logger.error('this approval has been handled')
        return HttpResponse(json.dumps(context), mimetype="application/json")

    group_request.delete()
    context = {
        'status': 1
    }
    logger.info('admin %s deny request %s of group %s', username, applicant_name, group_name)
    return HttpResponse(json.dumps(context), mimetype="application/json")


@login_required()
@csrf_exempt
def leave_group(request):
    username = request.user.username
    group_name = request.POST.get('group_name')
    logger.info('user %s leave group %s', username, group_name)

    user = User.objects.get(username=username)
    group = CollieGroup.objects.get(name=group_name)
    if group.has_admin(username):
        context = {
            'status': -1,
            'error': 'you are owner, can not leave'
        }
        logger.error('leave failed, coz user is owner of group')
        return HttpResponse(json.dumps(context), mimetype='application/json')

    user.groups.remove(group)
    logger.info('leave successfully')
    context = {
        'status': 1
    }
    return HttpResponse(json.dumps(context), mimetype="application/json")