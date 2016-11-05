import Queue
import base64
import copy
from email.mime.text import MIMEText
import smtplib
import dateutil
import json
import logging
from django.core.mail import EmailMessage
import os
import shutil
import re
import traceback
import urllib
import urllib2
import zipfile
import datetime
# from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
import time
from dateutil import tz, relativedelta
from django.views.defaults import permission_denied
from django.views.generic import TemplateView
from django_datatables_view.base_datatable_view import BaseDatatableView
from object_permissions import get_groups_any
from core.file_handler import checksum_file
from core.utils import get_file_content
from core.webhdfs import WebHdfs
from module.models import Module, ModuleVersions, ModuleHdfsFiles
from profiles.models import KerberosKeys, CollieGroup
from project.flows import ExecutionOptions, Job, Flow
from project.models import Project, ProjectVersions, ProjectFiles, ExecutionFlows, FlowLogs, ExecutionJobs, JobLogs, \
    Schedule, PROJECT_PERM_OWNER, PROJECT_PERM_USER
from settings import settings
from core.urllibr import encode

logger = logging.getLogger("collie")
COLLIEXE_EXECUTOR_URL = "http://" + settings.COLLIEXE_HOST + ":" + settings.COLLIEXE_PORT + "/executor"
COLLIEXE_SCHEDULE_URL = "http://" + settings.COLLIEXE_HOST + ":" + settings.COLLIEXE_PORT + "/schedule"
COLLIEXE_BROKERS_URL = "http://" + settings.COLLIEXE_HOST + ":" + settings.COLLIEXE_PORT + "/system"


@login_required()
def index(request):
    try:
        user = request.user
        username = user.username
        logger.info('project index page, user %s', username)

        if user.is_superuser:
            projects_valid = Project.objects.all()
        else:
            projects_valid = user.get_objects_any_perms(Project, perms=[PROJECT_PERM_OWNER, PROJECT_PERM_USER])

        projects = []
        for project in projects_valid:
            if project.status < 0:
                continue

            project_versions = ProjectVersions.objects.filter(project_id=project.id).order_by('-project_version')[:1]
            if len(project_versions) <= 0:
                continue
            project_version = project_versions[0]
            project_content = dict()
            project_content['project_name'] = project.name
            project_content['project_id'] = project_version.project_id
            project_content['project_version'] = project_version.project_version
            project_content['upload_user'] = project_version.upload_user
            project_content['upload_time'] = project_version.upload_time

            # found how many valid scheduled items
            project_id = project_version.project_id
            scheduled = Schedule.objects.filter(~Q(status='EXPIRED'), project_id=project_id)
            project_content['scheduled'] = len(scheduled)
            projects.append(project_content)

        context = {'project_list': projects}
        return render_to_response('project/project_index.html', context, context_instance=RequestContext(request))
    except Exception as e:
        logger.error("hit exception %s when get project index", e)
        raise


@login_required()
def manage_page(request):
    username = request.user.username
    logger.info("user %s visit project manage page", username)

    project_id = request.GET.get("project_id")
    version_id = request.GET.get("version_id")
    logger.info('get manage page, user %s, project %s, id %s', username, project_id, version_id)

    user = request.user
    project = Project.objects.get(id=project_id)
    if user.is_superuser:
        perms = [PROJECT_PERM_OWNER]
    else:
        perms = user.get_perms(project)

    if len(perms) <= 0:
        logger.error('no permission to enter')
        return permission_denied(request)

    if PROJECT_PERM_OWNER in perms:
        role = PROJECT_PERM_OWNER
    else:
        role = PROJECT_PERM_USER

    project_versions = ProjectVersions.objects.all().filter(project_id=project_id, project_version=version_id)
    project_version = project_versions.latest('project_version')
    diagram = project_version.diagram

    diagram_json = json.loads(diagram)
    jobs = diagram_json['jobs']
    connections = diagram_json['connections']

    # construct job info map
    job_info_map = {}
    for job in jobs:
        job_id = job['job_id']
        job_info_map[job_id] = job

    # found all job who has no followers
    job_has_follower_map = {}
    job_has_no_follower_map = {}
    for connection in connections:
        source_id = connection['source_id']
        job_has_follower_map[source_id] = True
    for job in jobs:
        job_id = job['job_id']
        if job_id in job_has_follower_map:
            continue
        job_has_no_follower_map[job_id] = job

    flows_root = []
    for job_id in job_has_no_follower_map.keys():
        job = job_info_map[job_id]

        # check there is schedule item of this flow
        schedule = Schedule.objects.filter(~Q(status='EXPIRED'), project_id=project_id, flow_id=job_id)
        has_scheduled = len(schedule) > 0
        flows_root.append({
            'job_id': job_id,
            'has_scheduled': has_scheduled,
            'name': job['name']
        })

    # get latest successful run date
    succeed_executions = ExecutionFlows.objects.filter(project_id=project.id, project_version=version_id,
                                                       status='SUCCEEDED').order_by('-end_time')
    latest_success_date = 'NA'
    if len(succeed_executions) > 0:
        latest_success_date = succeed_executions[0].end_time.replace(tzinfo=tz.gettz('Asia/Shanghai'))

    context = {
        'project': {
            'id': project.id,
            'version_id': version_id,
            'name': project.name,
            'permissions': 'ADMIN',
            'create_date': project.created_time,
            ### 'description': 'TODO',
            'modify_date': project_version.upload_time,
            # 'admins': '1.0',
            'latest_success_date': latest_success_date,
            'modify_by': project_version.upload_user,
            'role': role
        },
        'flows_root': flows_root
    }

    return render_to_response('project/project_manage.html', context, context_instance=RequestContext(request))


@login_required()
def page_edit_permission(request):
    project_id = request.GET.get('project_id')
    project = Project.objects.get(id=project_id)
    groups_owner = get_groups_any(project, perms=[PROJECT_PERM_OWNER])
    groups = []
    for group in groups_owner:
        groups.append({
            'name': group.name,
            'role': 'owner'
        })
    groups_user = get_groups_any(project, perms=[PROJECT_PERM_USER])
    for group in groups_user:
        groups.append({
            'name': group.name,
            'role': 'user'
        })
    context = {
        'groups': groups
    }
    return render_to_response('project/project_permission.html', context, context_instance=RequestContext(request))


@login_required()
@csrf_exempt
def grant_project_permission(request):
    username = request.user.username
    group_name = request.POST.get('group_name')
    project_id = request.POST.get('project_id')
    role = request.POST.get('role')
    logger.info('user %s grant group %s onto project id %s, role %s', username, group_name, project_id, role)

    if role != 'owner' and role != 'user':
        context = {
            'status': -1,
            'error': 'no such role found'
        }
        logger.error('failed to grant permission, coz no such role %s', role)
        return HttpResponse(json.dumps(context), mimetype='application/json')

    if role == 'owner':
        permission = PROJECT_PERM_OWNER
    else:
        permission = PROJECT_PERM_USER

    try:
        group = CollieGroup.objects.get(name=group_name)
    except ObjectDoesNotExist:
        context = {
            'status': -1,
            'error': 'no such group found'
        }
        logger.error('failed to grant permission, coz no such group %s', group_name)
        return HttpResponse(json.dumps(context), mimetype='application/json')

    project = Project.objects.get(id=project_id)
    group.revoke_all(project)
    group.grant(permission, project)
    context = {
        'status': 1
    }
    logger.info('successfully to grant permission')
    return HttpResponse(json.dumps(context), mimetype='application/json')


@login_required()
@csrf_exempt
def revoke_project_permission(request):
    user = request.user
    username = user.username
    project_id = request.POST.get('project_id')
    group_name = request.POST.get('group_name')
    logger.info('user %s revoke perm of group %s', username, group_name)

    try:
        group = CollieGroup.objects.get(name=group_name)
    except ObjectDoesNotExist:
        context = {
            'status': -1,
            'error': 'no such group found'
        }
        logger.error('failed to revoke permission, coz no such group %s', group_name)
        return HttpResponse(json.dumps(context), mimetype='application/json')

    project = Project.objects.get(id=project_id)
    group.revoke_all(project)
    context = {
        'status': 1
    }
    logger.info('successfully revoke permission')
    return HttpResponse(json.dumps(context), mimetype='application/json')


def get_proceedings(proceeding_map, current_id, job_info_map):
    if current_id not in proceeding_map:
        return []
    proceedings = proceeding_map[current_id]
    proceeding_infos = []
    for proceeding_job_id in proceedings['proceedings']:
        proceeding_info = get_proceedings(proceeding_map, proceeding_job_id, job_info_map)
        proceeding_infos.append({
            'job_id': proceeding_job_id,
            'name': job_info_map[proceeding_job_id]['name'],
            'proceedings': proceeding_info
        })
    return proceeding_infos


@login_required()
def flow_execute_options(request):
    username = request.user.username
    project_id = request.GET.get('project_id')
    version_id = request.GET.get('version_id')
    root_id = request.GET.get('job_id')
    flow_id = urllib2.unquote(root_id.encode("utf8"))
    logger.info("user %s enter to get execute/schedule page info, project id %s, version %s, root id %s",
                username, project_id, version_id, root_id)

    # get scheduled info when has scheduled
    scheduled_item = None
    if "is_edit_mode" in request.GET and request.GET.get("is_edit_mode") == 'true':
        logger.info("flow id %s", flow_id)
        scheduled = Schedule.objects.filter(~Q(status='EXPIRED'), project_id=project_id,
                                            project_version=version_id, flow_id=flow_id)
        if len(scheduled) <= 0:
            logger.error("flow scheduled item has been deleted")
            context = {
                'status': -1,
                'error': 'flow scheduled item has been deleted'
            }
            return HttpResponse(json.dumps(context), mimetype='application/json')
        scheduled_item = scheduled[0]

    project_versions = ProjectVersions.objects.filter(project_id=project_id, project_version=version_id)
    project_version = project_versions.latest('project_version')
    diagram = project_version.diagram
    diagram_json = json.loads(diagram)

    # initialize jobs_info and connections map
    job_info_map, job_proceeding_map = dict(), dict()
    for job in diagram_json['jobs']:
        job_id = job['job_id']
        job_info_map[job_id] = job
    for connection in diagram_json['connections']:
        source_id = connection['source_id']
        target_id = connection['target_id']
        if target_id not in job_proceeding_map:
            job_proceeding_map[target_id] = []
        job_proceeding_map[target_id].append(source_id)

    # figure out flow jobs & connections
    mandatory_hadoop = False
    has_yarn_job = False
    yarn_clusters = []
    flow_jobs, flow_connections, visited_jobs = list(), list(), list()
    flow_jobs_queue = Queue.Queue()
    flow_jobs_queue.put(flow_id.decode("utf8"))
    visited_jobs.append(flow_id.decode("utf8"))
    while not flow_jobs_queue.empty():
        flow_job = flow_jobs_queue.get()
        job_info = job_info_map[flow_job]
        if not mandatory_hadoop or not has_yarn_job:
            version_id = job_info['module_version']
            module_version = ModuleVersions.objects.get(id=version_id)
            version_type = module_version.type
            if version_type == 'Shell' and not mandatory_hadoop:
                module_options = json.loads(module_version.options)
                if 'hadoop_support' in module_options:
                    mandatory_hadoop = module_options['hadoop_support']
            if (version_type == 'yarn' or version_type == 'spark') and not has_yarn_job:
                mandatory_hadoop = True
                has_yarn_job = True
                for cluster in settings.YARN_CLUSTERS.split(","):
                    yarn_clusters.append(cluster)
        flow_jobs.append(job_info)
        if flow_job not in job_proceeding_map:
            continue
        for proceeding_id in job_proceeding_map[flow_job]:
            flow_connections.append({
                'source_id': proceeding_id,
                'target_id': flow_job
            })
            if proceeding_id not in visited_jobs:
                flow_jobs_queue.put(proceeding_id)
                visited_jobs.append(proceeding_id)

    # align relative relation of jobs
    least_top = 9999999999.9
    least_left = 9999999999.9
    total_top = 0.0
    total_left = 0.0
    for job in flow_jobs:
        job_top = float(job['top'][0:-2])
        job_left = float(job['left'][0:-2])
        total_top += job_top
        total_left += job_left
        if job_top < least_top:
            least_top = job_top
        if job_left < least_left:
            least_left = job_left

    least_left -= 10.0
    least_top -= 15.0
    for job in flow_jobs:
        job['top'] = str(float(job['top'][0:-2]) - least_top) + 'px'
        job['left'] = str(float(job['left'][0:-2]) - least_left) + 'px'

    # get kerberos keys
    kerberos_keys = KerberosKeys.objects.filter(username=username)
    kkeys = []
    if not kerberos_keys is None:
        for kerberos_key in kerberos_keys:
            kkeys.append({
                'name': kerberos_key.name
            })

    # get scheduled info when has scheduled
    if scheduled_item:
        flow_data = json.loads(scheduled_item.flow_data)
        scheduled_info = {
            'flow_data': flow_data,
            'period': scheduled_item.period,
            'first_check_time': scheduled_item.first_check_time
        }
    else:
        scheduled_info = None

    context = {
        'status': 1,
        'username': username,
        'jobs': flow_jobs,
        'connections': flow_connections,
        'kkeys': kkeys,
        'mandatory_hadoop': mandatory_hadoop,
        'has_yarn_job': has_yarn_job,
        'yarn_clusters': yarn_clusters,
        'scheduled_info': scheduled_info
    }

    return HttpResponse(json.dumps(context), mimetype='application/json')


def flow_colliexe_nodes(request):
    colliexe_node = []
    req_parameters = {
        'action': 'cluster'
    }
    try:
        req_response = urllib2.urlopen(COLLIEXE_BROKERS_URL + "?%s" % (urllib.urlencode(req_parameters)), timeout=1).\
            read()
    except urllib2.URLError as e:
        context = {
            'context': -1,
            'error': 'no available running node found'
        }
        return HttpResponse(json.dumps(context), mimetype='application/json')

    req_response = json.loads(req_response)
    logger.info(req_response)

    if 'success' in req_response:
        nodes_str = req_response['success']
        nodes = nodes_str.split(',')
        for node in nodes:
            node_info = node.split(':')
            node_id = node_info[0]
            # node_ip = node_info[1]
            node_host = node_info[2]
            colliexe_node.append({
                'id': node_id,
                'host': node_host
            })
        context = {
            'status': 1,
            'colliexe_nodes': colliexe_node
        }
    elif 'error' in req_response:
        context = {
            'status': -1,
            'error': req_response['error']
        }

    return HttpResponse(json.dumps(context), mimetype='application/json')


@login_required()
@csrf_exempt
def flow_schedule(request):
    username = request.user.username
    project_id = request.POST.get('project_id')
    version_id = request.POST.get('version_id')
    flow_jobs = request.POST.get('flow_jobs')
    options = json.loads(request.POST.get('options'))
    schedule_options_str = request.POST.get('schedule_options')
    is_edit_mode = request.POST.get('is_edit_mode')
    logger.info("user %s schedule project %s, version %s, options %s, edit %s", username, project_id, version_id,
                options, is_edit_mode)

    schedule_options = json.loads(schedule_options_str)
    flow_jobs_json = json.loads(flow_jobs)

    project_versions = ProjectVersions.objects.all().filter(project_id=project_id, project_version=version_id)\
        .order_by('-project_version')
    project_version = project_versions[0]
    project_diagram = project_version.diagram
    project_diagram_json = json.loads(project_diagram)

    # get root job of current flow
    connections = project_diagram_json['connections']
    following_map = {}
    flow_root_job_id = None
    for connection in connections:
        source_id = connection['source_id']
        target_id = connection['target_id']
        if source_id not in following_map:
            following_map[source_id] = []
        following_map[source_id].append(target_id)
    for job_id in flow_jobs_json:
        if job_id not in following_map:
            flow_root_job_id = job_id
            break
    flow_root_job = get_job_by_id(project_diagram_json['jobs'], flow_root_job_id)

    flow_data = get_flow_data(project_id,
                              '',
                              project_version.project_version,
                              flow_root_job['name'],
                              flow_jobs_json,
                              options,
                              username)

    date_time_date_raw = schedule_options['datetime']
    try:
        date_time = datetime.datetime.strptime(date_time_date_raw, "%Y/%m/%d %H:%M")
    except ValueError:
        date_time = datetime.datetime.strptime(date_time_date_raw, "%Y-%m-%d %H:%M")

    date_time_str = date_time.strftime('%Y-%m-%dT%H:%M:00')

    # delete old schedule info when is edit mode
    schedule_item = None
    if is_edit_mode == 'true':
        scheduled = Schedule.objects.filter(~Q(status='EXPIRED'), project_id=project_id,
                                            project_version=version_id, flow_id=job_id)
        for schedule in scheduled:
            req_parameters = {
                'action': 'del',
                'scheduleId': schedule.id
            }
            req_response = urllib2.urlopen(COLLIEXE_SCHEDULE_URL + "?%s" % (urllib.urlencode(req_parameters)))\
                .read()
            logger.info("delete schedule %d, response %s", schedule.id, req_response)
            schedule_item = schedule

    # get request parameters
    req_parameters = {
        'action': 'add',
        'projectId': project_id,
        'projectVersion': version_id,
        'flowId': flow_root_job['job_id'],
        'flowData': flow_data,
        'datetime': date_time_str,
        'user': username,
        'recurring': schedule_options['recurring'],
        'period': schedule_options['period_number'] + schedule_options['period_unit']
    }

    # colliexe node
    colliexe_node_id = options['colliexe_node_id']
    if colliexe_node_id >= 0:
        req_parameters['nodeId'] = colliexe_node_id

    # run schedule url api
    req_response = urllib2.urlopen(COLLIEXE_SCHEDULE_URL + "?%s" % (urllib.urlencode(req_parameters))).read()
    logger.info(req_response)
    req_response = json.loads(req_response)

    # send notification email
    if is_edit_mode == 'true' and schedule_item:
        send_schedule_changed_mail(schedule_item)

    if 'success' in req_response:
        res_json = {"status": 1}
    else:
        res_json = {"status": -1, "error": json.loads(req_response)['error']}
    return HttpResponse(json.dumps(res_json), mimetype='application/json')


def flow_tree(request):
    project_id = request.GET.get("project_id")
    root_job_id = request.GET.get("job_id")
    project_versions = ProjectVersions.objects.filter(project_id=project_id)
    project_version = project_versions.latest('project_version')
    diagram = project_version.diagram
    diagram_json = json.loads(diagram)

    # construct job info map
    job_info_map = {}
    for job in diagram_json['jobs']:
        job_id = job['job_id']
        job_info_map[job_id] = job

    # construct proceeding map
    proceeding_map = {}
    for connection in diagram_json['connections']:
        source_id = connection['source_id']
        target_id = connection['target_id']
        if target_id in proceeding_map:
            proceeding_map[target_id]['proceedings'].append(source_id)
        else:
            proceeding_map[target_id] = {}
            proceeding_map[target_id]['proceedings'] = []
            proceeding_map[target_id]['proceedings'].append(source_id)

    job_info = job_info_map[root_job_id]
    res_data = dict()
    res_data['job_id'] = root_job_id
    res_data['name'] = job_info['name']
    res_data['proceedings'] = get_proceedings(proceeding_map, root_job_id, job_info_map)

    res_json = {"status": 1, "data": json.dumps(res_data)}
    return HttpResponse(json.dumps(res_json), mimetype='application/json')


@login_required()
def flow_index(request):
    username = request.user.username
    logger.info("user %s visit flow index page", username)

    project_id = request.GET.get('project_id')
    version_id = request.GET.get('version_id')
    job_id = request.GET.get('job_id')
    project = Project.objects.get(id=project_id)
    project_versions = ProjectVersions.objects.filter(project_id=project_id, project_version=version_id)
    project_version = project_versions[0]
    project_name = project.name
    project_diagram = project_version.diagram
    project_diagram_json = json.loads(project_diagram)

    jobs = project_diagram_json['jobs']
    job = get_job_by_id(jobs, job_id)
    # module_id = job['module_id']
    # module = Module.objects.get(id=module_id)
    flows = ExecutionFlows.objects.filter(project_id=project_id, flow_id=job_id).order_by('-execution_id')[:50]

    flows_info = []
    for flow_info in flows:
        status = flow_info.status
        if status == 'SUCCEEDED':
            badge_class = 'badge-success'
        elif status == 'CANCELLED':
            badge_class = 'badge-default'
        elif status == 'FAILED':
            badge_class = 'badge-important'
        elif status == 'RUNNING':
            badge_class = 'badge-info'
        else:
            badge_class = 'badge-warning'
        start_time = flow_info.start_time
        end_time = flow_info.end_time

        if start_time is None or end_time is None:
            elapsed = None
        else:
            elapsed = end_time - start_time
            start_time = start_time.replace(tzinfo=tz.gettz('Asia/Shanghai'))
            end_time = end_time.replace(tzinfo=tz.gettz('Asia/Shanghai'))
        flows_info.append({
            'execution_id': flow_info.execution_id,
            'badge_class': badge_class,
            'status': flow_info.status,
            'submit_user': flow_info.submit_user,
            'submit_time': flow_info.submit_time,
            'start_time': start_time,
            'end_time': end_time,
            'elapsed': elapsed
        })

    # check there is scheduled of this flow
    scheduled = Schedule.objects.filter(~Q(status='EXPIRED'), project_id=project_id, project_version=version_id, flow_id=job_id)
    has_scheduled = len(scheduled) > 0
    context = {
        'project_id': project_id,
        'project_version': project_version.project_version,
        'project_name': project_name,
        'job_name': job['name'],
        'flows_info': flows_info,
        'has_scheduled': has_scheduled
    }
    return render_to_response('project/project_flow_index.html', context, context_instance=RequestContext(request))


def flow_diagram(request):
    try:
        project_id = request.GET.get('project_id')
        version_id = request.GET.get('version_id')
        flow_root_job_id = request.GET.get('flow_id')
        project_version = ProjectVersions.objects.filter(project_id=project_id, project_version=version_id)[:1].get()
        diagram = json.loads(project_version.diagram)

        jobs = diagram['jobs']
        connections = diagram['connections']

        # construct job info map
        job_info_map = {}
        for job in jobs:
            job_info_map[urllib2.quote(job['job_id'].encode('utf8'))] = job
            # job_info_map[encode(job['job_id'].encode('utf8'))] = job

        # construct in connections
        in_connections_map = {}
        for connection in connections:
            target_id = encode(connection['target_id'].encode('utf8'))
            if target_id not in in_connections_map:
                in_connections_map[target_id] = []
            in_connections_map[target_id].append(connection)

        # get essential jobs and connections
        jobs_res = []
        connections_res = []
        queue = Queue.Queue()
        visited_jobs = list()
        # flow_root_job_id = urllib2.unquote(flow_root_job_id)
        visited_jobs.append(flow_root_job_id)
        queue.put(flow_root_job_id)
        while not queue.empty():
            job_id = queue.get()
            logger.info("job id %s, map %s", job_id, job_info_map)
            job = job_info_map[job_id]
            jobs_res.append(job)
            if job_id not in in_connections_map:
                continue
            in_connections = in_connections_map[job_id]
            for in_connection in in_connections:
                connections_res.append(in_connection)
                preceding_job = encode(in_connection['source_id'].encode('utf8'))
                if preceding_job not in visited_jobs:
                    queue.put(preceding_job)
                    visited_jobs.append(preceding_job)

        context = {
            'status': 1,
            'jobs': jobs_res,
            'connections': connections_res
        }
        return HttpResponse(json.dumps(context), mimetype='application/json')
    except Exception as e:
        logger.error("Hit exception %s", e)
        raise


@login_required()
def flow_execution_diagram(request):
    try:
        execution_id = request.GET.get('execution_id')
        execution_flow = ExecutionFlows.objects.get(execution_id=execution_id)
        project_id = execution_flow.project_id
        version_id = execution_flow.project_version
        flow_root_job_id = execution_flow.flow_id
        project_version = ProjectVersions.objects.filter(project_id=project_id, project_version=version_id)[:1].get()
        logger.info("get execution flow diagram, project id %s, project version %s", project_id, version_id)
        diagram = json.loads(project_version.diagram)

        jobs = diagram['jobs']
        connections = diagram['connections']

        # construct job info map
        job_info_map = {}
        execution_flow_jobs = json.loads(execution_flow.flow_data)['jobs']
        for job in jobs:
            job_id = job['job_id']
            if job_id in execution_flow_jobs.keys() and 'ignoreFailed' in execution_flow_jobs[job_id]:
                job['ignore_failed'] = execution_flow_jobs[job_id]['ignoreFailed']
            job_info_map[job['job_id']] = job

        # construct incoming connections
        in_connections_map = {}
        for connection in connections:
            target_id = connection['target_id']
            if target_id not in in_connections_map:
                in_connections_map[target_id] = []
            in_connections_map[target_id].append(connection)

        # get essential jobs and connections
        jobs_res = []
        connections_res = []
        queue = Queue.Queue()
        visited_jobs = list()
        visited_jobs.append(flow_root_job_id)
        queue.put(flow_root_job_id)
        while not queue.empty():
            job_id = queue.get()
            job = job_info_map[job_id]
            job_res = copy.deepcopy(job)
            job_name = job_res['name']
            execution_jobs = ExecutionJobs.objects.filter(execution_id=execution_id, job_id=job_name)
            logger.info("get execution job info for job_id %s", job_name)
            if len(execution_jobs) <= 0:
                jobs = json.loads(execution_flow.flow_data)['jobs']
                status = 'ready'
                if job_name in jobs.keys():
                    job_info = jobs[job_name]
                    if job_info['jobStatus'] == 'DISABLED':
                        status = 'DISABLED'
            else:
                status = execution_jobs[0].status

            job_res['status'] = status
            jobs_res.append(job_res)
            if job_id not in in_connections_map:
                continue
            in_connections = in_connections_map[job_id]
            for in_connection in in_connections:
                connections_res.append(in_connection)
                preceding_job = in_connection['source_id']
                if preceding_job not in visited_jobs:
                    queue.put(in_connection['source_id'])
                    visited_jobs.append(preceding_job)

        execution_status = execution_flow.status

        context = {
            'status': 1,
            'execution_status': execution_status,
            'jobs': jobs_res,
            'connections': connections_res
        }
        return HttpResponse(json.dumps(context), mimetype='application/json')
    except Exception as e:
        logger.error("hit exception, %s", e)


def execution_index(request):
    try:
        execution_id = request.GET.get('execution_id')
        execution_flow = ExecutionFlows.objects.get(execution_id=execution_id)
        flow_id = execution_flow.flow_id
        flow_status = execution_flow.status
        project_versions = ProjectVersions.objects.filter(project_id=execution_flow.project_id,
                                                          project_version=execution_flow.project_version)
        project_version = project_versions[0]
        project_diagram = json.loads(project_version.diagram)
        project = Project.objects.get(id=project_version.project_id)

        # get flow name by flow_id (equal with job_id)
        jobs = project_diagram['jobs']
        flow_name = ''
        for job in jobs:
            job_id = job['job_id']
            if job_id == flow_id:
                flow_name = job['name']
                break

        # get running / done jobs list
        execution_jobs_raw = ExecutionJobs.objects.all().filter(execution_id=execution_id).order_by('start_time')
        execution_jobs = []

        # start_time
        execution_start_time = ExecutionFlows.objects.get(execution_id=execution_id).start_time
        if not execution_start_time is None:
            execution_start_time = execution_start_time.replace(tzinfo=tz.gettz('Asia/Shanghai'))
        else:
            execution_start_time = datetime.datetime.utcnow().replace(tzinfo=tz.gettz('UTC'))
        # end_time
        execution_end_time = ExecutionFlows.objects.get(execution_id=execution_id).end_time
        if execution_end_time is None:
            execution_end_time = datetime.datetime.utcnow().replace(tzinfo=tz.gettz('UTC'))
        else:
            execution_end_time = execution_end_time.replace(tzinfo=tz.gettz('Asia/Shanghai'))
        # total seconds
        time_elapse = execution_end_time - execution_start_time
        total_seconds = time_elapse.days * 86400 + time_elapse.seconds
        if total_seconds <= 0:  # fix bug: float division by zero
            total_seconds = 1
        # calculate each job
        for execution_job in execution_jobs_raw:
            start_time = execution_job.start_time
            start_time = start_time.replace(tzinfo=tz.gettz('Asia/Shanghai'))
            end_time = execution_job.end_time
            if end_time is None:
                end_time = execution_end_time
            else:
                end_time = end_time.replace(tzinfo=tz.gettz('Asia/Shanghai'))
            elapsed = end_time - start_time
            elapsed_seconds = elapsed.days * 86400 + elapsed.seconds
            run_elapse = start_time - execution_start_time
            waiting_run_seconds = run_elapse.days * 86400 + run_elapse.seconds
            timeline_run_width = (elapsed_seconds / float(total_seconds)) * 100
            timeline_waiting_width = (waiting_run_seconds / float(total_seconds)) * 100
            status = execution_job.status
            job_name = execution_job.job_id
            # execution_job_diagram = get_job_by_name(jobs, job_name)
            execution_jobs.append({
                'job_name': job_name,
                'job_id': urllib.quote(job_name.encode('utf-8')),
                'timeline': 0,
                'timeline_width': str(timeline_run_width) + '%',
                'timeline_margin_left': str(timeline_waiting_width) + '%',
                'start_time': start_time,
                'end_time': end_time,
                'elapsed': elapsed,
                'badge_class': get_badge_class(status),
                'status': status
            })

        # get flow log
        if flow_status == 'SUCCEEDED' or flow_status == 'FAILED' or flow_status == 'CANCELLED' or flow_status == 'READY':
            if flow_status != 'READY':
                try:
                    flow_logs = FlowLogs.objects.get(execution_id=execution_id)
                    log = flow_logs.log
                except ObjectDoesNotExist:
                    log = ''
            else:
                log = ''
            context = {
                'execution_id': execution_id,
                'flow_name': flow_name,
                'project_id': project_version.project_id,
                'project_version': project_version.project_version,
                'flow_id': flow_id,
                'project_name': project.name,
                'execution_jos': execution_jobs,
                'log_offset': 0,
                'log_data': log,
            }
        else:
            # get running log
            req_parameters = {
                'action': 'log',
                'type': 'flow',
                'execId': execution_id,
                'offset': 0,
                'length': 10000  # 10KB
            }
            req = urllib.urlencode(req_parameters)
            req_response = urllib2.urlopen(COLLIEXE_EXECUTOR_URL, req).read()
            logger.info(req_response)

            req_response_json = json.loads(req_response)
            if 'log' in req_response_json:
                log_offset = req_response_json['log']['offset'] + req_response_json['log']['length']
                log_data = req_response_json['log']['data']
            else:
                log_offset = 0
                log_data = req_response_json['error']
                logger.error('hit error when get execution index, %s', log_data)

            context = {
                'execution_id': execution_id,
                'flow_name': flow_name,
                'project_id': project_version.project_id,
                'project_version': project_version.project_version,
                'flow_id': flow_id,
                'project_name': project.name,
                'execution_jos': execution_jobs,
                'log_offset': log_offset,
                'log_data': log_data,
            }

        return render_to_response('project/project_flow_execution.html', context,
                                  context_instance=RequestContext(request))
    except Exception as e:
        logger.error("unexpected error! %s", e)
        raise


@login_required()
def flow_execution_log(request):
    execution_id = request.GET.get('execution_id')
    execution_flow = ExecutionFlows.objects.get(execution_id=execution_id)
    flow_status = execution_flow.status

    # get flow log
    if flow_status == 'SUCCEEDED' or flow_status == 'FAILED' or flow_status == 'CANCELLED' or flow_status == 'READY':
        if flow_status != 'READY':
            flow_logs = FlowLogs.objects.get(execution_id=execution_id)
            log = flow_logs.log
        else:
            log = ''
        context = {
            'status': 1,
            'log_offset': 0,
            'log_data': log,
        }
    else:
        # get running log
        req_parameters = {
            'action': 'log',
            'type': 'flow',
            'execId': execution_id,
            'offset': 0,
            'length': 500000000  # 500M
        }
        req = urllib.urlencode(req_parameters)
        req_response = urllib2.urlopen(COLLIEXE_EXECUTOR_URL, req).read()
        req_response_json = json.loads(req_response)
        context = {
            'status': 1,
            'log_offset': req_response_json['log']['offset'] + req_response_json['log']['length'],
            'log_data': req_response_json['log']['data'],
        }

    return HttpResponse(json.dumps(context), mimetype='application/json')


def execution_job_index(request):
    try:
        execution_id = request.GET.get('execution_id')
        job_name = request.GET.get('job_id')

        execution = ExecutionFlows.objects.get(execution_id=execution_id)
        project_id = execution.project_id
        project = Project.objects.get(id=project_id)
        version_id = execution.project_version
        project_version = ProjectVersions.objects.filter(project_id=project_id, project_version=version_id)[:1].get()
        diagram = json.loads(project_version.diagram)
        flow_root_job = get_job_by_id(diagram['jobs'], execution.flow_id)

        execution_status = execution.status
        if execution_status == 'SUCCEEDED' or execution_status == 'FAILED' or execution_status == 'CANCELLED':
            try:
                job_log = JobLogs.objects.get(execution_id=execution_id, job_id=job_name)
                log_data = job_log.log
            except ObjectDoesNotExist:
                log_data = ""

            # get log from db
            context = {
                'execution_id': execution_id,
                'project_name': project.name,
                'flow_name': flow_root_job['name'],
                'project_id': project.id,
                'project_version': project_version.project_version,
                'flow_id': execution.flow_id,
                'job_name': job_name,
                'log_offset': 0,
                'log_data': log_data
            }
        else:
            req_parameters = {
                'action': 'log',
                'type': 'job',
                'execId': execution_id,
                'jobId': job_name,
                'offset': 0,
                'length': 500000000  # 500M
            }
            req_data = urllib.urlencode(req_parameters)
            req_response = urllib2.urlopen(COLLIEXE_EXECUTOR_URL, req_data).read()
            logger.debug(req_response)
            req_response = json.loads(req_response)
            if 'data' in req_response['log']:
                req_response_data = req_response['log']['data']
            else:
                req_response_data = ''

            # get log from remote server
            context = {
                'execution_id': execution_id,
                'project_name': project.name,
                'flow_name': flow_root_job['name'],
                'project_id': project.id,
                'project_version': project_version.project_version,
                'flow_id': execution.flow_id,
                'job_name': job_name,
                'log_offset': 0,
                'log_data': req_response_data
            }
        return render_to_response('project/project_flow_execution_job.html', context,
                                  context_instance=RequestContext(request))
    except Exception as e:
        logger.error('Hit exception when get execution job index page, %s', e)
        raise


@login_required()
def execution_job_log(request):
    try:
        username = request.user.username
        execution_id = request.GET.get('execution_id')
        job_name = request.GET.get('job_id')
        logger.info('get job log %s, user %s', job_name, username)

        job_name = urllib2.unquote(job_name)
        execution = ExecutionFlows.objects.get(execution_id=execution_id)
        execution_status = execution.status

        if execution_status == 'SUCCEEDED' or execution_status == 'FAILED' or execution_status == 'CANCELLED':
            logger.debug('execution_id=' + execution_id + " job_id=" + job_name)
            try:
                job_log = JobLogs.objects.get(execution_id=execution_id, job_id=job_name)
                log_data = job_log.log
            except ObjectDoesNotExist:
                log_data = ""

            # get log from db
            context = {
                'status': 1,
                'log_offset': 0,
                'log_data': log_data
            }
        else:
            req_parameters = {
                'action': 'log',
                'type': 'job',
                'execId': execution_id,
                'jobId': job_name,
                'offset': 0,
                'length': 500000000  # 500M
            }
            req_data = urllib.urlencode(req_parameters)
            req_response = urllib2.urlopen(COLLIEXE_EXECUTOR_URL, req_data).read()
            req_response = json.loads(req_response)
            if 'data' in req_response['log']:
                req_response_data = req_response['log']['data']
            else:
                req_response_data = ''
            # get log from remote server
            context = {
                'status': 1,
                'log_offset': 0,
                'log_data': req_response_data
            }
        return HttpResponse(json.dumps(context), mimetype='application/json')
    except Exception as e:
        logger.error('hit Exception, %s', e)
        raise


@login_required()
@csrf_exempt
def new_project(request):
    username = request.user.username
    project_name = request.POST.get('project_name')
    logger.info('user %s create project %s', username, project_name)

    project = Project.create(project_name, username)
    user = User.objects.get(username=username)
    user.grant(PROJECT_PERM_OWNER, project)

    context = {
        'status': 1,
        'project_id': project.id
    }
    logger.info('succeed to create project, res %s', context)
    return HttpResponse(json.dumps(context), mimetype='application/json')


@login_required()
def edit_project(request):
    username = request.user.username
    project_id = request.GET.get('project_id')

    project = Project.objects.get(id=project_id)
    modules = []
    for module in Module.objects.all().filter(status__gte=0):
        module_id = module.id
        module_versions = ModuleVersions.objects.filter(module_id=module_id, status__gte=0).values('id')
        if len(module_versions) <= 0:
            continue
        module_created_by = module.created_by
        module_is_public = module.is_public
        if module_created_by != username and not module_is_public:
            continue
        modules.append({'id': module.id, 'name': module.name})
    context = {
        'module_list': modules,
        'project_name': project.name,
        'project_id': project.id}
    return render_to_response('project/project_edit.html', context, context_instance=RequestContext(request))


@login_required()
@csrf_exempt
def save_project(request):
    try:
        username = request.user.username
        project_id = request.POST.get("project_id")
        project_diagram = request.POST.get("diagram")
        project = Project.objects.get(id=project_id)
        logger.info('user %s save project %s', username, project.name)
        log_current_ms("start")

        project.diagram = project_diagram
        project.save()
        log_current_ms("save diagram")

        # create temp folder (name: project_id)
        tmp_path = settings.PROJECT_SAVE_PATH + "tmp/" + str(project.id)
        if not os.path.exists(tmp_path):
            logger.info("tmpPath is created" + tmp_path)
            os.makedirs(tmp_path)
        log_current_ms("make temp path")

        # delete all folders and files under that temp folder
        for the_file in os.listdir(tmp_path):
            file_path = os.path.join(tmp_path, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.exists(file_path):
                    shutil.rmtree(file_path)
            except Exception, e:
                logger.error(e)
        log_current_ms("delete old files")

        # parse the diagram files, get module id & file
        # download module files under that temp folder from database
        current_diagram_json = json.loads(project_diagram)
        jobs = current_diagram_json["jobs"]
        job_file_name_map = {}
        job_info_map = {}
        module_version_info_map = {}
        module_version_file_checksum_map = {}
        for job in jobs:
            job_id = job["job_id"]
            job_info_map[job_id] = job
            # job_module_id = job["module_id"]
            module_version_id = job["module_version"]
            log_current_ms("download " + job["name"] + " - get before")
            module_version = ModuleVersions.objects.get(id=module_version_id)
            log_current_ms("download " + job["name"] + " - get after")
            module_version_info_map[module_version_id] = module_version
            module_type = module_version.type
            module_file = module_version.file
            module_file_name = module_version.file_name
            hdfs_file_id = module_version.hdfs_file_id

            module_version_folder = ""
            if settings.REPOSITORY_SAVE_MODE == settings.REPOSITORY_SAVE_MODE_HDFS and hdfs_file_id > 0:
                hdfs_file = ModuleHdfsFiles.objects.get(id=hdfs_file_id)
                file_name = hdfs_file.name.strip()
                checksum = hdfs_file.checksum.strip()
                hdfs_path = hdfs_file.path.strip()
                module_version_folder = tmp_path + "/modules/" + checksum + "/"
                if not os.path.exists(module_version_folder):
                    os.makedirs(module_version_folder)
                webhdfs = WebHdfs()
                logger.info("starting to copy remote to local, %s -> %s", hdfs_path, module_version_folder)
                webhdfs.copyToLocal(hdfs_path, module_version_folder)
                local_file_path_old = module_version_folder + file_name + "_" + checksum
                local_file_path_new = module_version_folder + file_name
                logger.info("rename file from %s -> %s", local_file_path_old, local_file_path_new)
                os.rename(local_file_path_old, local_file_path_new)
                module_version_file_checksum_map[module_version_id] = checksum
            else:
                job_file_name_map[job_id] = module_file_name
                log_current_ms("download " + job["name"] + " - b64d before")
                module_file_content = base64.b64decode(module_file)
                log_current_ms("download " + job["name"] + " - b64d after")
                file_temp_folder = tmp_path + "/modules/temp/"
                if not os.path.exists(file_temp_folder):
                    os.makedirs(file_temp_folder)

                version_file = open(file_temp_folder + module_file_name, "wb+")
                version_file.write(module_file_content)
                version_file.close()
                checksum = checksum_file(open(file_temp_folder + module_file_name, "r"))

                module_version_folder = tmp_path + "/modules/" + checksum + "/"
                module_version_file_checksum_map[module_version_id] = checksum

                if os.path.exists(module_version_folder):
                    shutil.rmtree(file_temp_folder)
                    continue

                os.rename(file_temp_folder, module_version_folder)
            if module_type == 'Shell' or module_type == 'Jar':
                # unzip module_file
                zip_file = zipfile.ZipFile(module_version_folder + module_file_name)
                for sub_file in zip_file.infolist():
                    zip_file.extract(sub_file, module_version_folder)
                # remove unused zip file
                os.remove(module_version_folder + "/" + module_file_name)
                log_current_ms("download " + job["name"] + " - zip extract")
        log_current_ms("download module files")

        # generate .job files according to diagram detail info
        connections = current_diagram_json["connections"]

        # construct proceeding map
        proceeding_map = {}
        for connection in connections:
            source_id = connection["source_id"]
            target_id = connection["target_id"]
            if target_id not in proceeding_map:
                proceeding_map[target_id] = []
            proceeding_map[target_id].append(source_id)

        # at first, generate job who has proceeding
        for job_id in proceeding_map.keys():
            job_info = job_info_map[job_id]
            job_name = job_info['name']
            job_conf_file = open(tmp_path + "/" + job_name + ".job", 'w')

            # write all conf exclude dependencies
            write_job_conf(job_conf_file, job_id,
                           job_info_map, module_version_info_map, module_version_file_checksum_map)

            # write dependencies out
            proceedings = proceeding_map[job_id]
            dependencies = []
            for proceeding in proceedings:
                proceeding_name = job_info_map[proceeding]['name']
                dependencies.append(proceeding_name)
            job_conf_file.write('dependencies=' + ','.join(dependencies) + '\n')

            # close config file
            job_conf_file.close()
        log_current_ms("write job config file")

        # then, generate job who has no proceeding
        for job in jobs:
            job_id = job['job_id']
            if job_id in proceeding_map:  # filter job who has proceeding
                continue

            # write all config
            job_conf_file = open(tmp_path + "/" + job['name'] + ".job", 'w')
            write_job_conf(job_conf_file, job_id,
                           job_info_map, module_version_info_map, module_version_file_checksum_map)

            # close config file
            job_conf_file.close()
        log_current_ms("write job config file2")

        # zip the file & read zip content & save on project files
        project_name = project.name
        zipf_path = tmp_path + "/../" + project_name + ".zip"
        zipf = zipfile.ZipFile(zipf_path, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True)
        zipdir(tmp_path, "", zipf)
        zipf.close()
        log_current_ms("zip project version package")

        # copy project package to hdfs
        project_version_id = int(round(time.time()))
        project_hdfs_path = ""
        if settings.REPOSITORY_SAVE_MODE == settings.REPOSITORY_SAVE_MODE_HDFS:
            webhdfs = WebHdfs()
            project_hdfs_path = settings.PROJECT_HDFS_ROOT + str(project_version_id) + ".zip"
            webhdfs.copyFromLocal(zipf_path, project_hdfs_path)
            os.remove(zipf_path)

        # project file
        project_version = ProjectVersions(project_id=project_id,
                                          project_version=project_version_id,
                                          diagram=project_diagram,
                                          upload_user=username,
                                          upload_time=datetime.datetime.now(tz=tz.gettz('Asia/Shanghai')),
                                          hdfs_path=project_hdfs_path,
                                          file_type="zip",
                                          file_name=project_name + ".zip",
                                          md5="",
                                          num_chunks=1)
        project_version.save()
        log_current_ms("save project version")

        change_module_version_ref_count_by_add_project_version(project_id)
        log_current_ms("change module version count")

        if settings.REPOSITORY_SAVE_MODE == settings.REPOSITORY_SAVE_MODE_DB:
            file_encode = base64.b64encode("".join(get_file_content(zipf_path)))
            log_current_ms("save project file - encode base64")
            project_file = ProjectFiles(project_id=project_id,
                                        project_version=project_version.project_version,
                                        chunk=0,
                                        file=file_encode)
            project_file.save()
            log_current_ms("save project file")

        # automatically re-schedule flow which preview scheduled on this project
        message = ""
        schedules = Schedule.objects.filter(~Q(status='EXPIRED'), project_id=project_id)
        if len(schedules) > 0:
            for scheduled_item in schedules:
                scheduled_flow_data = json.loads(scheduled_item.flow_data)
                scheduled_flow_jobs = scheduled_flow_data["jobs"]
                scheduled_flow_root_id = scheduled_item.flow_id

                # delete stale schedule
                req_parameters = {
                    'action': 'del',
                    'scheduleId': scheduled_item.id}
                req_response = urllib2.urlopen(COLLIEXE_SCHEDULE_URL + "?%s" % (urllib.urlencode(req_parameters)))\
                    .read()
                logger.info("delete schedule %d, response %s", scheduled_item.id, req_response)

                current_flow_jobs = get_flow_jobs(current_diagram_json, scheduled_flow_root_id)
                if not current_flow_jobs or len(current_flow_jobs) != len(scheduled_flow_jobs):
                    message += "<p>flow <span class=\"label label-warning\">" + scheduled_item.flow_id + "</span> diagram has changed, " \
                               "scheduled info is deleted automatically.</p>"
                    send_schedule_deleted_mail(scheduled_item)
                    continue

                if not keep_same_flow(current_diagram_json, scheduled_flow_data):
                    message += "<p>flow <span class=\"label label-warning\">" + scheduled_item.flow_id + "</span> diagram has changed, " \
                               "scheduled info is deleted automatically.</p>"
                    send_schedule_deleted_mail(scheduled_item)
                    continue

                # invoke add schedule
                scheduled_flow_data["projectVersion"] = project_version.project_version
                req_parameters = {
                    'action': 'add',
                    'projectId': project_id,
                    'projectVersion': project_version.project_version,
                    'flowId': scheduled_item.flow_id,
                    'flowData': json.dumps(scheduled_flow_data),
                    'datetime': scheduled_item.first_check_time,
                    'user': scheduled_item.schedule_user,
                    'recurring': not scheduled_item.period,
                    'period': scheduled_item.period,
                    'nodeId': scheduled_flow_data['nodeId']
                }

                req_response = urllib2.urlopen(COLLIEXE_SCHEDULE_URL + "?%s" % (urllib.urlencode(req_parameters)))\
                    .read()
                logger.info(req_response)

                Schedule.objects.update()
                scheduled_item = Schedule.objects.filter(~Q(status='EXPIRED'), project_id=project_id,
                                                         project_version=project_version.project_version,
                                                         flow_id=scheduled_item.flow_id)[0]
                send_schedule_applied_to_version_email(scheduled_item)
                message += "</p>flow <span class=\"label label-info\">" + scheduled_item.flow_id + \
                           "</span> scheduled info applied to new version automatically.</p>"

        log_current_ms("reschedule project")

        # delete unused project files if on db mode
        if settings.REPOSITORY_SAVE_MODE == settings.REPOSITORY_SAVE_MODE_DB:
            ProjectFiles.objects.filter(~Q(project_version=project_version.project_version),
                                        project_id=project_id).delete()

        context = {
            "status": 1,
            "project_id": project_id,
            "project_version": project_version.project_version,
            "name": str(project.name.encode("utf-8")),
            "message": message
        }
        return HttpResponse(json.dumps(context), mimetype='application/json')
    except AttributeError as e:
        logger.error(e)
        context = {
            "status": -1,
            "error": 'please re-login again.'
        }
        return HttpResponse(json.dumps(context), mimetype='application/json')
    except Exception as e:
        traceback.print_exc()
        logger.error('unexpected error: %s', e)
        context = {
            "status": -1,
            "error": "server internal error"
        }
        return HttpResponse(json.dumps(context), mimetype='application/json')


def keep_same_flow(newest_diagram_json, scheduled_flow_json):
    flow_id = scheduled_flow_json["flowId"]

    # construct incoming connections
    newest_preceding_map = {}
    for connection in newest_diagram_json["connections"]:
        source_id = connection['source_id']
        target_id = connection['target_id']

        if source_id == flow_id:
            logger.info("flow id : %s is not root of flow anymore", flow_id)
            return False

        if target_id not in newest_preceding_map:
            newest_preceding_map[target_id] = []
        newest_preceding_map[target_id].append(source_id)
    for job in newest_diagram_json["jobs"]:
        job_id = job["job_id"]
        if job_id not in newest_preceding_map:
            newest_preceding_map[job_id] = []

    # construct preceding jobs map from scheduled flow data
    scheduled_jobs = scheduled_flow_json["jobs"]
    scheduled_preceding_map = {}
    for scheduled_job in scheduled_jobs.keys():
        scheduled_job_json = scheduled_jobs[scheduled_job]
        scheduled_preceding_map[scheduled_job] = []
        if "ancestors" not in scheduled_job_json:
            continue
        preceding_jobs = scheduled_job_json["ancestors"]
        for preceding_job in preceding_jobs:
            scheduled_preceding_map[scheduled_job].append(preceding_job)

    # get essential jobs and connections
    queue = Queue.Queue()
    queue.put(flow_id)
    visited_jobs = list()
    visited_jobs.append(flow_id)
    while not queue.empty():
        job_id = queue.get()
        if job_id not in scheduled_preceding_map:
            continue

        # check whether same preceding jobs between scheduled & current project version
        scheduled_preceding_jobs = scheduled_preceding_map[job_id]
        newest_preceding_jobs = newest_preceding_map[job_id]
        if len(scheduled_preceding_jobs) != len(newest_preceding_jobs):
            return False
        for scheduled_preceding_job in scheduled_preceding_jobs:
            job_existed = False
            for newest_preceding_job in newest_preceding_jobs:
                if scheduled_preceding_job == newest_preceding_job:
                    job_existed = True
                    break
            if not job_existed:
                return False

        preceding_jobs_in_scheduled = scheduled_preceding_map[job_id]
        for preceding_job in preceding_jobs_in_scheduled:
            if preceding_job not in visited_jobs:
                queue.put(preceding_job)
                visited_jobs.append(preceding_job)

    return True


def get_flow_jobs(diagram_json, flow_root_job_id):
    jobs_res = []
    connections = diagram_json["connections"]

    # construct incoming connections
    in_connections_map = {}
    for connection in connections:
        target_id = connection['target_id']
        if target_id not in in_connections_map:
            in_connections_map[target_id] = []
        in_connections_map[target_id].append(connection)

    # find root job by job id
    jobs = diagram_json["jobs"]
    found_root = False
    for job in jobs:
        job_id = job["job_id"]
        if job_id == flow_root_job_id:
            found_root = True
            break
    if not found_root:
        logger.info("could not find root job by id")
        return None

    # get essential jobs and connections
    queue = Queue.Queue()
    queue.put(flow_root_job_id)
    visited_jobs = list()
    visited_jobs.append(flow_root_job_id)
    while not queue.empty():
        job_id = queue.get()
        jobs_res.append(job_id)

        if job_id not in in_connections_map:
            continue
        in_connections = in_connections_map[job_id]
        for in_connection in in_connections:
            preceding_job = in_connection['source_id']
            if preceding_job not in visited_jobs:
                queue.put(preceding_job)
                visited_jobs.append(preceding_job)

    return jobs_res


def write_job_conf(job_conf_file, job_id, job_info_map, module_version_info_map, module_version_file_checksum_map):
    job_info = job_info_map[job_id]

    job_module_version_id = job_info['module_version']
    job_module_version = module_version_info_map[job_module_version_id]
    module_type = job_module_version.type
    version_file_checksum = module_version_file_checksum_map[job_module_version_id]

    # set working dir
    job_conf_file.write('working.dir=modules/' + version_file_checksum + '/\n')

    if module_type == 'Shell':
        module_options = json.loads(job_module_version.options)
        job_conf_file.write('type=shell\n')
        job_conf_file.write('command=sh ' + module_options['main_script'] + '\n')

        module_args = {} if 'args' not in module_options else module_options['args']
        job_args = {} if 'options' not in job_info or 'args' not in job_info['options'] \
            else job_info['options']['args']
        write_args(module_args, job_args, 'shell.param.', job_conf_file)

    elif module_type == 'Jar':
        module_options = json.loads(job_module_version.options)
        job_conf_file.write('type=java\n')
        job_conf_file.write('java.class=' + module_options['java_class'] + '\n')
        if 'classpath' in module_options and not module_options['classpath'] == '':
            job_conf_file.write('classpath=' + module_options['classpath'] + '\n')
        if 'Xms' in module_options and not module_options['Xms'] == '':
            job_conf_file.write('Xms=' + module_options['Xms'] + '\n')
        if 'Xmx' in module_options and not module_options['Xmx'] == '':
            job_conf_file.write('Xmx=' + module_options['Xmx'] + '\n')

        module_main_args = module_options['main_args']
        job_main_args = {} if 'options' not in job_info or 'main_args' not in job_info['options'] \
            else job_info['options']['main_args']
        write_args(module_main_args, job_main_args, 'main.args.', job_conf_file)

        module_jvm_args = module_options['jvm_args']
        job_jvm_args = {} if 'options' not in job_info or 'jvm_args' not in job_info['options'] \
            else job_info['options']['jvm_args']
        write_args(module_jvm_args, job_jvm_args, 'jvm.args.', job_conf_file)

    elif module_type == 'yarn':
        module_options = json.loads(job_module_version.options)
        job_conf_file.write('type=yarn\n')
        job_conf_file.write('jar=' + job_module_version.file_name + '\n')
        job_conf_file.write('java.class=' + module_options['main_class'] + '\n')

        module_main_args = module_options['main_args']
        job_main_args = {} if 'options' not in job_info or 'main_args' not in job_info['options'] \
            else job_info['options']['main_args']
        write_args(module_main_args, job_main_args, 'main.args.', job_conf_file)

        module_jvm_args = module_options['jvm_args']
        job_jvm_args = {} if 'options' not in job_info or 'jvm_args' not in job_info['options'] \
            else job_info['options']['jvm_args']
        write_args(module_jvm_args, job_jvm_args, 'jvm.args.', job_conf_file)

    elif module_type == 'spark':
        module_options = json.loads(job_module_version.options)
        job_conf_file.write('type=spark\n')
        job_conf_file.write('jar=' + job_module_version.file_name + '\n')
        job_conf_file.write('java.class=' + module_options['spark_class'] + '\n')

        module_spark_args = module_options['spark_args']
        job_spark_args = {} if 'options' not in job_info or 'spark_args' not in job_info['options'] \
            else job_info['options']['spark_args']
        write_args(module_spark_args, job_spark_args, 'spark.args.', job_conf_file)


def write_args(module_args, job_args, arg_prefix, job_conf_file):
    key_index_map = {}
    for arg in module_args:
        arg_name = arg["name"]

        key_index = 0
        if arg_name in key_index_map:
            key_index = key_index_map[arg_name]

        found_index = 0
        found_value = None
        for option in job_args:
            option_key = option['key']
            if option_key == arg_name:
                if key_index == found_index:
                    found_value = option['value']
                    key_index_map[arg_name] = key_index + 1
                    break
                else:
                    found_index += 1

        if not found_value:
            continue

        arg_value = found_value
        job_conf_file.write(arg_prefix + arg_name + "=" + arg_value + "\n")

@login_required()
@csrf_exempt
def delete(request):
    project_id = request.POST.get('project_id')
    project = Project.objects.get(id=project_id)
    project.status = -1
    project.save()

    change_module_version_ref_count_by_delete_project(project_id)
    res_json = {"status": 1}
    return HttpResponse(json.dumps(res_json), mimetype='application/json')


@login_required()
@csrf_exempt
def rename(request):
    username = request.user.username
    project_id = request.POST.get('project_id')
    project_name = request.POST.get('name')
    logger.info("user %s renames project %s to %s", username, project_id, project_name)

    project = Project.objects.get(id=project_id)
    project.name = project_name
    project.save()

    context = {
        'status': 1
    }
    return HttpResponse(json.dumps(context), mimetype='application/json')


def detail(request):
    project_id = request.GET.get('project_id')
    version_id = request.GET.get('project_version')
    project_version = ProjectVersions.objects.filter(project_id=project_id, project_version=version_id)[:1].get()
    res_json = {
        'status': 1,
        'diagram': json.loads(project_version.diagram)
    }
    return HttpResponse(json.dumps(res_json), mimetype='application/json')


@login_required()
@csrf_exempt
def flow_execute(request):
    username = request.user.username
    project_id = request.POST.get("project_id")
    version_id = request.POST.get("version_id")
    flow_jobs = request.POST.get("flow_jobs")
    options = json.loads(request.POST.get("options"))
    flow_jobs_json = json.loads(flow_jobs)

    project_versions = ProjectVersions.objects.all().filter(project_id=int(project_id), project_version=int(version_id))
    project_version = project_versions[0]
    project_diagram = project_version.diagram
    project_diagram_json = json.loads(project_diagram)

    # get root job of current flow
    jobs = project_diagram_json['jobs']
    connections = project_diagram_json['connections']
    follower_map = {}
    flow_root = None
    for connection in connections:
        source_id = connection['source_id']
        target_id = connection['target_id']
        if source_id not in follower_map:
            follower_map[source_id] = []
        follower_map[source_id].append(target_id)
    for job in flow_jobs_json:
        if job not in follower_map:
            flow_root = job
            break
    flow_root_job = get_job_by_id(jobs, flow_root)

    execution_flow = ExecutionFlows(node_id=1,
                                    project_id=project_id,
                                    project_version=project_version.project_version,
                                    flow_id=flow_root,
                                    flow_data="",
                                    encoding_type="plain",
                                    status="READY",
                                    submit_user=username)
    execution_flow.save()
    flow_data = get_flow_data(project_id,
                              execution_flow.execution_id,
                              project_version.project_version,
                              execution_flow.flow_id,
                              flow_jobs_json,
                              options,
                              username)
    execution_flow.flow_data = flow_data
    execution_flow.save()

    # invoke run http url
    req_parameters = {
        'action': 'execute',
        'execId': execution_flow.execution_id,
        'flowId': flow_root_job['name'].encode('utf-8')
    }
    # colliexe node
    colliexe_node_id = options['colliexe_node_id']
    if colliexe_node_id >= 0:
        req_parameters['nodeId'] = colliexe_node_id

    req = urllib2.Request(COLLIEXE_EXECUTOR_URL, urllib.urlencode(req_parameters))
    try:
        req_response = urllib2.urlopen(req).read()
        logger.info(req_response)
        status = 1
        message = ''
    except urllib2.URLError as e:
        status = -1
        message = e.reason.strerror

    res_json = {"status": status, "message": message, "execution_id": execution_flow.execution_id}
    return HttpResponse(json.dumps(res_json), mimetype='application/json')


@csrf_exempt
def execution_pause(request):
    execution_id = request.POST.get('execution_id')
    req_parameters = {
        'action': 'pause',
        'execId': execution_id,
        'user': 'fake_user'
    }
    req_data = urllib.urlencode(req_parameters)
    req_response = urllib2.urlopen(COLLIEXE_EXECUTOR_URL, req_data).read()
    req_response = json.loads(req_response)

    if 'success' in req_response:
        res_json = {"status": 1}
    else:
        res_json = {"status": 0, 'error': req_response['error']}
    return HttpResponse(json.dumps(res_json), mimetype='application/json')


@csrf_exempt
def execution_cancel(request):
    execution_id = request.POST.get('execution_id')
    exection_flows = ExecutionFlows.objects.get(execution_id=execution_id)
    req_parameters = {
        'action': 'cancel',
        'execId': execution_id,
        'user': 'fake_user'  # exection_flows.submit_user
    }
    req_data = urllib.urlencode(req_parameters)
    req_response = urllib2.urlopen(COLLIEXE_EXECUTOR_URL, req_data).read()
    req_response = json.loads(req_response)

    if 'success' in req_response:
        res_json = {"status": 1}
    else:
        res_json = {"status": -1, "error": req_response['error']}
    return HttpResponse(json.dumps(res_json), mimetype='application/json')


@csrf_exempt
def execution_resume(request):
    execution_id = request.POST.get('execution_id')
    exection_flows = ExecutionFlows.objects.get(execution_id=execution_id)
    req_parameters = {
        'action': 'resume',
        'execId': execution_id,
        'user': 'fake_user'  # exection_flows.submit_user
    }
    req_data = urllib.urlencode(req_parameters)
    req_response = urllib2.urlopen(COLLIEXE_EXECUTOR_URL, req_data).read()
    req_response = json.loads(req_response)

    if 'success' in req_response:
        res_json = {"status": 1}
    else:
        res_json = {"status": 0, "error": req_response["error"]}
    return HttpResponse(json.dumps(res_json), mimetype='application/json')


@login_required()
def download(request):
    project_name = request.GET.get("name")
    project_zip_path = "/tmp/collie-projects/" + project_name + ".zip"
    file_content = []
    with open(project_zip_path, 'rb') as f:
        while 1:
            byte_s = f.read(1)
            if not byte_s:
                break
            byte = byte_s[0]
            file_content.append(byte)

    # generate the file
    response = HttpResponse(file_content, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=' + project_name + '.zip'
    return response


@login_required()
def executing_page(request):
    user = request.user
    username = user.username
    logger.info('enter executing page, user %s', username)

    running_flows = ExecutionFlows.objects.filter(status='RUNNING')
    running_list = []
    for running_flow in running_flows:
        project_id = running_flow.project_id
        project = Project.objects.get(id=running_flow.project_id)

        # verify has perm
        if not user.has_any_perms(project) and not user.is_superuser:
            continue

        version_id = running_flow.project_version
        project_version = ProjectVersions.objects.filter(project_id=project_id, project_version=version_id)[:1].get()
        diagram = json.loads(project_version.diagram)
        flow_root_job = get_job_by_id(diagram['jobs'], running_flow.flow_id)
        running_list.append({
            'id': running_flow.execution_id,
            'flow': flow_root_job['name'],
            'project_id': project.id,
            'project_version': project_version.project_version,
            'flow_id': running_flow.flow_id,
            'project': project.name,
            'user': running_flow.submit_user,
            'proxy_user': running_flow.submit_user,
            'start_time': running_flow.start_time.replace(tzinfo=tz.gettz('Asia/Shanghai'))
        })
    context = {
        'executing_list': running_list
    }
    return render_to_response('project/project_executing.html', context, context_instance=RequestContext(request))


class HistoryView(TemplateView):
    template_name = 'project/project_history.html'


class HistoryDataTableView(BaseDatatableView):
    model = ExecutionFlows
    columns = ['execution_id', 'flow_id', 'project_id', 'project_version', 'submit_user',
               'start_time', 'end_time', 'status']
    order_columns = ['execution_id', 'start_time', 'end_time']

    def get_initial_queryset(self):
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable
        # You should not filter data returned here by any filter values entered by user. This is because
        # we need some base queryset to count total number of records.
        user = self.request.user
        logger.info("enter history page, user %s", user.username)
        # get all projects has perms
        if user.is_superuser:
            projects = Project.objects.all()
        else:
            projects = user.get_objects_any_perms(Project, perms=[PROJECT_PERM_OWNER, PROJECT_PERM_USER])
        project_ids = []
        for project in projects:
            project_ids.append(project.id)
        return ExecutionFlows.objects.filter(project_id__in=project_ids)

    def filter_queryset(self, qs):
        search = self.request.GET.get('sSearch', None)
        if search:
            qs = qs.filter(Q(project_id__contains=search) | Q(execution_id__contains=search))
        return qs

    def prepare_results(self, qs):
        # prepare list with output column data
        json_data = []
        for item in qs:
            try:
                job_id = item.flow_id
                project_id = item.project_id
                version_id = item.project_version
                project = Project.objects.get(id=project_id)
                project_version = ProjectVersions.objects.filter(project_id=project_id, project_version=version_id)[:1]\
                    .get()
                diagram = json.loads(project_version.diagram)
                job = get_job_by_id(diagram['jobs'], job_id)
                flow_name = ''
                if not job is None:
                    flow_name = job['name']
                start_time = item.start_time
                end_time = item.end_time
                if start_time is None:
                    elapsed = ''
                elif end_time is None:
                    # TODO: subtract local 8 hours
                    elapsed = timezone.now() - item.start_time - datetime.timedelta(hours=-8)
                else:
                    elapsed = end_time - item.start_time

                # get start time & end time in local timezone
                if not start_time is None:
                    start_time = start_time.replace(tzinfo=tz.gettz('Asia/Shanghai'))
                if not end_time is None:
                    end_time = end_time.replace(tzinfo=tz.gettz('Asia/Shanghai'))

                badge_class = get_badge_class(item.status)
            except (ValueError, ObjectDoesNotExist, TypeError) as e:
                logger.error(e)
                continue

            json_data.append([
                # Execution ID
                "<a href='/project/execution/index?execution_id=" + str(item.execution_id) + "'>" +
                str(item.execution_id) +
                "</a>",
                # Flow Name
                "<a href='/project/flow/index?project_id=" + str(item.project_id) +
                "&version_id=" + str(item.project_version) + "&job_id=" + str(item.flow_id) + "'>" + flow_name +
                "</a>",
                # Project Name
                "<a href='/project/manage?project_id=" + str(item.project_id) +
                "&version_id=" + str(item.project_version) + "'>" + project.name +
                "</a>",
                # User
                item.submit_user,
                # Start Time
                start_time,
                # End Time
                end_time,
                # Elapsed
                #elapsed,
                str(elapsed),
                # Status
                "<span class='badge " + badge_class + "'>" + item.status + "</span>"
            ])
        return json_data


@login_required()
def scheduled_page(request):
    try:
        user = request.user
        username = user.username
        logger.info('enter schedule page, user %s', username)

        scheduled_items_db = Schedule.objects.filter(Q(status='READY') | Q(status='RUNNING') | Q(status='SLEEPING'))
        scheduled_items_res = []
        for scheduled_item_db in scheduled_items_db:
            scheduled_item_res = {}
            project_id = scheduled_item_db.project_id
            project = Project.objects.get(id=project_id)
            project_version = scheduled_item_db.project_version
            flow_id = scheduled_item_db.flow_id
            scheduled_item_res['project_id'] = project_id

            # verify has perm
            if not user.has_any_perms(project) and not user.is_superuser:
                continue

            # initialize
            project_versions = ProjectVersions.objects.filter(project_id=project_id, project_version=project_version)
            project_version = project_versions[0]
            diagram = json.loads(project_version.diagram)
            flow_root_job = get_job_by_id(diagram['jobs'], flow_id)
            logger.info("get job %s by flow id %s", flow_root_job, flow_id)
            if not flow_root_job:
                continue

            scheduled_item_res['id'] = scheduled_item_db.id
            scheduled_item_res['project_id'] = scheduled_item_db.project_id
            scheduled_item_res['project_version'] = scheduled_item_db.project_version
            scheduled_item_res['flow_id'] = scheduled_item_db.flow_id
            scheduled_item_res['flow_name'] = flow_root_job['name']
            scheduled_item_res['submitted_user'] = scheduled_item_db.schedule_user
            scheduled_item_res['badge_class'] = get_badge_class(scheduled_item_db.status)
            scheduled_item_res['status'] = scheduled_item_db.status
            # get project name
            scheduled_item_res['project_name'] = project.name

            # calculate next execution time
            scheduled_item_res['first_scheduled_run'] = scheduled_item_db.first_check_time
            recurring_option_pattern = re.compile('([0-9]+)([Mwdhms])')
            recurring_option_match = recurring_option_pattern.match(scheduled_item_db.period)
            if recurring_option_match is None:
                scheduled_item_res['next_execution_time'] = None
                scheduled_item_res['repeats_every'] = None
            else:
                scheduled_item_res['repeats_every'] = scheduled_item_db.period
                time_current_datetime = datetime.datetime.now(tz.gettz('Asia/Shanghai'))
                time_first_str = scheduled_item_db.first_check_time
                time_first_datetime_nozone = datetime.datetime.strptime(time_first_str, '%Y-%m-%dT%H:%M:%S')
                time_first_datetime = time_first_datetime_nozone.replace(tzinfo=tz.gettz('Asia/Shanghai'))
                recurring_number = recurring_option_match.group(1)
                recurring_period = recurring_option_match.group(2)

                if recurring_period == 'M':
                    elapsed_delta = dateutil.relativedelta.relativedelta(time_current_datetime - time_first_datetime)
                    elapsed_months = elapsed_delta.years * 12 + elapsed_delta.months
                    time_gossip = time_first_datetime + dateutil.relativedelta.relativedelta(
                        months=+int(elapsed_months / float(recurring_number)) * float(recurring_number))
                    time_next_execution = time_gossip
                    if time_gossip < time_current_datetime:
                        time_next_execution = time_gossip + dateutil.relativedelta\
                            .relativedelta(months=+int(recurring_number))
                    scheduled_item_res['next_execution_time'] = time_next_execution
                else:
                    time_current_elapse = time_current_datetime.replace(tzinfo=None) - datetime.datetime(1970, 1, 1)
                    time_current_seconds = time_current_elapse.days * 86400 + time_current_elapse.seconds
                    time_first_elapse = time_first_datetime_nozone - datetime.datetime(1970, 1, 1)
                    time_first_seconds = time_first_elapse.days * 86400 + time_first_elapse.seconds
                    elapsed_seconds = time_current_seconds - time_first_seconds
                    unit_seconds = 1
                    if recurring_period == 'w':
                        unit_seconds = 7 * 24 * 60 * 60
                    elif recurring_period == 'd':
                        unit_seconds = 24 * 60 * 60
                    elif recurring_period == 'h':
                        unit_seconds = 60 * 60
                    elif recurring_period == 'm':
                        unit_seconds = 60

                    if time_first_seconds > time_current_seconds:
                        seconds_gossip = time_first_seconds
                    else:
                        recurring_seconds = int(recurring_number) * unit_seconds
                        seconds_gossip = time_first_seconds + int(elapsed_seconds / recurring_seconds) * recurring_seconds
                        if seconds_gossip < time_current_seconds:
                            seconds_gossip += recurring_seconds
                    seconds_next_execution = seconds_gossip
                    seconds_next_execution -= 8 * 60 * 60  # TODO: add local timezone offset for Beijing
                    # convert long to datetime
                    time_next_execution = datetime.datetime.fromtimestamp(seconds_next_execution)
                    scheduled_item_res['next_execution_time'] = time_next_execution
                scheduled_item_res['has_sla'] = False  # TODO: fix later
            scheduled_items_res.append(scheduled_item_res)
        context = {
            'scheduled_items': scheduled_items_res
        }
        return render_to_response('project/project_scheduled.html', context, context_instance=RequestContext(request))
    except Exception, ex:
        traceback.print_exc()
        logger.error("hit exception when get scheduled page. %s", ex)
        raise ex


@login_required()
@csrf_exempt
def scheduled_delete(request):
    username = request.user.username
    scheduled_id = request.POST.get('scheduled_id')
    logger.info("user %s delete schedule, id %s", username, scheduled_id)

    try:
        scheduled_item = Schedule.objects.get(id=scheduled_id)
    except ObjectDoesNotExist:
        pass

    req_parameters = {
        'action': 'del',
        'scheduleId': scheduled_id
    }
    req_response = urllib2.urlopen(COLLIEXE_SCHEDULE_URL + "?%s" % (urllib.urlencode(req_parameters))).read()
    logger.info(req_response)

    # send notification email
    if scheduled_item:
        send_schedule_deleted_mail(scheduled_item)

    context = {'status': 1}
    return HttpResponse(json.dumps(context), mimetype='application/json')


def zipdir(root, relative_path, zip):
    path = os.path.join(root, relative_path)
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)):
            os.chdir(root)
            zip.write(os.path.join(relative_path, item))
        if os.path.isdir(os.path.join(path, item)):
            zipdir(root, os.path.join(relative_path, item), zip)


def get_flow_data(project_id, execution_id, project_version, flow_id, flow_jobs, options, username):
    # flow_jobs data structure
    # key : job_id
    # value : status (READY / DISABLED)

    project_versions = ProjectVersions.objects.filter(project_id=project_id, project_version=project_version)
    project_diagram_str = project_versions[0].diagram
    project_diagram = json.loads(project_diagram_str)

    project_jobs = project_diagram["jobs"]
    project_connections = project_diagram["connections"]

    job_info_map = {}
    for job in project_jobs:
        job_info_map[job["job_id"]] = job

    jobs = list()
    proceeding_map = {}
    for connection in project_connections:
        source_id = connection["source_id"]
        target_id = connection["target_id"]
        if target_id not in proceeding_map:
            proceeding_map[target_id] = []
        proceeding_map[target_id].append(source_id)

    # add job who has proceeding
    for follower in proceeding_map.keys():
        if follower not in flow_jobs:
            continue
        proceedings = proceeding_map[follower]

        follower_job = job_info_map[follower]
        job = Job()
        status = flow_jobs[follower]['status']
        job.job_status = status
        ignore_failed = flow_jobs[follower]['ignore_failed']
        job.ignore_failed = ignore_failed
        job.job_id = follower_job['name']
        # job.job_type = 'shell'
        job.job_source = follower_job['name'] + '.job'

        proceeding_names = []
        for proceeding_id in proceedings:
            proceeding_job = job_info_map[proceeding_id]
            proceeding_names.append(proceeding_job['name'])
        job.ancestors = proceeding_names
        jobs.append(job)
    # add job who has no proceedings
    for job_id in flow_jobs:
        if job_id in proceeding_map:  # job has proceeding
            continue
        job_info = job_info_map[job_id]
        job = Job()
        status = flow_jobs[job_id]['status']
        job.job_status = status
        ignore_failed = flow_jobs[job_id]['ignore_failed']
        job.ignore_failed = ignore_failed
        job.job_id = job_info['name']
        # job.job_type = 'shell'
        job.job_source = job_info['name'] + '.job'
        jobs.append(job)

    execution = ExecutionOptions()
    execution.notify_on_first_failure = options['notify_on_first_failure']
    execution.notify_on_last_failure = options['notify_on_last_failure']
    execution.failure_emails_override = options['failure_emails_override']
    execution.failure_emails = options['failure_emails'].split(',')
    execution.success_emails_override = options['success_emails_override']
    execution.success_emails = options['success_emails'].split(',')

    execution.flow_parameters = {}
    # yarn cluster
    yarn_cluster = options['yarn_cluster']
    if yarn_cluster:
        execution.flow_parameters['yarnCluster'] = yarn_cluster
    # queue name
    queue_name = options['queue_name']
    if queue_name != 'default':
        execution.flow_parameters['queueName'] = queue_name
    # kerberos key
    kerberos_key = options['kerberos_key']
    if kerberos_key != 'None':
        execution.flow_parameters['kerberosKey'] = kerberos_key
        execution.flow_parameters['kerberosUser'] = username

    # failure action
    failure_action_val = options['failure_action']
    if failure_action_val == 'finish_currently_running':
        failure_action = ExecutionOptions.FAILURE_ACTION_FINISH_CURRENTLY_RUNNING
    elif failure_action_val == 'cancel_all':
        failure_action = ExecutionOptions.FAILURE_ACTION_CANCEL_ALL
    elif failure_action_val == 'finish_all_possible':
        failure_action = ExecutionOptions.FAILURE_ACTION_FINISH_ALL_POSSIBLE
    execution.failure_action = failure_action
    # concurrent option
    if options['concurrent_option_skip']:
        concurrent_option = ExecutionOptions.CONCURRENT_OPTION_SKIP
    elif options['concurrent_option_ignore']:
        concurrent_option = ExecutionOptions.CONCURRENT_OPTION_IGNORE
    elif options['concurrent_option_pipeline']:
        concurrent_option = ExecutionOptions.CONCURRENT_OPTION_PIPELINE
    execution.concurrent_option = concurrent_option
    execution.pipeline_level = options['pipeline_level']

    project_flow = Flow()
    if 'colliexe_node_id' in options:
        project_flow.node_id = options['colliexe_node_id']
    project_flow.execution_id = execution_id
    project_flow.project_id = project_id
    project_flow.project_version = project_version
    project_flow.submit_user = username
    project_flow.submit_time = int(round(time.time() * 1000))
    project_flow.flow_id = flow_id
    project_flow.flow_status = "READY"
    project_flow.jobs = jobs
    project_flow.execution_options = execution

    return project_flow.dump_to_json()


def get_job_by_id(jobs, job_id):
    for job in jobs:
        job_id_tmp = job["job_id"]
        if job_id_tmp == job_id:
            return job
    return None


def get_job_by_name(jobs, job_name):
    for job in jobs:
        job_name_tmp = job["name"]
        if job_name_tmp == job_name:
            return job
    return None


def get_badge_class(status):
    if status == 'SUCCEEDED':
        badge_class = 'badge-success'
    elif status == 'CANCELLED' or status == 'SLEEPING':
        badge_class = 'badge-default'
    elif status == 'FAILED':
        badge_class = 'badge-important'
    elif status == 'RUNNING':
        badge_class = 'badge-info'
    else:
        badge_class = 'badge-warning'
    return badge_class


def change_module_version_ref_count_by_add_project_version(project_id):
    # get latest project versions
    project_versions = ProjectVersions.objects.filter(project_id=project_id).values('project_version', 'diagram')\
        .order_by('-upload_time')
    if len(project_versions) <= 0:
        return
    log_current_ms("get project versions")

    # latest_version
    if len(project_versions) >= 1:
        latest_version = project_versions[0]
        diagram = json.loads(latest_version['diagram'])
        jobs = diagram['jobs']
        for job in jobs:
            version_id = job['module_version']
            module_versions = ModuleVersions.objects.filter(id=version_id)
            module_version = module_versions.values("id", "refer_count")[0]
            log_current_ms("change refer count of latest(" + job["name"] + "-" + str(module_version["id"]) + ")-get")
            module_versions.update(refer_count=int(module_version["refer_count"]) + 1)
            log_current_ms("change refer count of latest(" + job["name"] + "-" + str(module_version["id"]) + ")-save")
    log_current_ms("change refer count of latest")

    # penultimate_version (last 2nd version)
    if len(project_versions) >= 2:
        penultimate_version = project_versions[1]
        diagram = json.loads(penultimate_version['diagram'])
        jobs = diagram['jobs']
        for job in jobs:
            version_id = job['module_version']
            module_versions = ModuleVersions.objects.filter(id=version_id)
            module_version = module_versions.values("id", "refer_count")[0]
            log_current_ms("refer count of penultimate(" + job["name"] + "-" + str(module_version["id"]) + ")-get")
            module_versions.update(refer_count=int(module_version["refer_count"]) - 1)
            log_current_ms("refer count of penultimate(" + job["name"] + "-" + str(module_version["id"]) + ")-save")
    log_current_ms("change refer count of penultimate")

    return


def change_module_version_ref_count_by_delete_project(project_id):
    # get latest project versions
    project_versions = ProjectVersions.objects.filter(project_id=project_id).values('project_version', 'diagram')\
        .order_by('-upload_time')
    if len(project_versions) <= 0:
        return

    # latest_version
    if len(project_versions) >= 1:
        latest_version = project_versions[0]
        diagram = json.loads(latest_version['diagram'])
        jobs = diagram['jobs']
        for job in jobs:
            version_id = job['module_version']
            module_version = ModuleVersions.objects.get(id=version_id)
            module_version.refer_count -= 1
            module_version.save()
    return


last_ms = 0


def log_current_ms(stage):
    global last_ms
    current_ms = int(round(time.time() * 1000))
    logger.info("%s : %d, %d", stage, current_ms - last_ms, current_ms)
    last_ms = current_ms


def send_schedule_deleted_mail(scheduled_item):
    subject = "Flow '%s' schedule has been deleted on Collie" % scheduled_item.flow_id
    message = "<html><h2>%s</h2><a href=\"http://%s/project/manage?project_id=%s&version_id=%s\">" \
              "Check On Collie</a></html>" % (subject, settings.EMAIL_BASE_URL,
                                              scheduled_item.project_id, scheduled_item.project_version)
    send_schedule_mail_3(scheduled_item, subject, message)


def send_schedule_changed_mail(scheduled_item):
    subject = "Flow '%s' schedule has been changed on Collie" % scheduled_item.flow_id
    send_schedule_mail_2(scheduled_item, subject)


def send_schedule_applied_to_version_email(scheduled_item):
    subject = "Flow '%s' schedule has been applied to new version on Collie" % scheduled_item.flow_id
    send_schedule_mail_2(scheduled_item, subject)


def send_schedule_mail_2(scheduled_item, subject):
    message = "<html><h2>%s</h2><a href=\"http://%s/project/flow/index?project_id=%s&version_id=%s&job_id=%s\">" \
              "Check Schedule On Collie</a></html>" % (subject, settings.EMAIL_BASE_URL,
                                                       scheduled_item.project_id, scheduled_item.project_version,
                                                       scheduled_item.flow_id)
    send_schedule_mail_3(scheduled_item, subject, message)


def send_schedule_mail_3(scheduled_item, subject, message):
    success_emails = json.loads(scheduled_item.flow_data)["executionOptions"]["successEmails"]
    failure_emails = json.loads(scheduled_item.flow_data)["executionOptions"]["failureEmails"]
    notify_emails = set(success_emails + failure_emails)
    msg = MIMEText(message, _subtype='html', _charset='utf-8')
    msg['Subject'] = subject
    msg['To'] = ",".join(notify_emails)
    s = smtplib.SMTP()
    s.connect(settings.EMAIL_HOST)
    s.sendmail(settings.EMAIL_FROM, notify_emails, msg.as_string())
    s.close()
