# -*- coding: UTF-8 -*-

# Create your views here.
import json
import logging
import traceback
import urllib
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
import sys
from django.utils import timezone
from core.http_client import WebHdfsException
from core.webhdfs import WebHdfs
from table.hive_table_operator import HiveTableOperator
from table.models import ExistedTable
import httplib
from settings import settings

reload(sys)
sys.setdefaultencoding('utf-8')


logger = logging.getLogger("collie")


@login_required()
def index(request):
    data = ""

    context = {'table_data': data}
    return render_to_response('table/table_index.html', context, context_instance=RequestContext(request))


@login_required()
def create(request):
    context = {}
    return render_to_response('table/table_create.html', context, context_instance=RequestContext(request))


def create_table(request):
    '''
    table_name
    table_comment
    columns
      column_tag
      column_name
      column_comment
      column_type
      column_is_partition
    '''
    logger.info("table create, info %s", request.POST.get("table_info"))

    # construct
    table_info = json.loads(str(request.POST.get("table_info")))
    operator = HiveTableOperator()
    operator.create_table(table_info)
    '''
    service_id = table_info['service_id']
    table_name = table_info['name']
    table_comment = table_info['comment']
    logger.info("table info: service id %s, name %s, comment %s", service_id, table_name, table_comment)
    table_columns = table_info['columns']
    for column in table_columns:
        column_tag = column['tag']
        column_name = column['name']
        column_comment = column['comment']
        column_type = column['type']
        column_is_partition = column['is_partition']
        logger.info("column info: tag %s, name %s, comment %s, type %s, is_partition %s",
                    column_tag, column_name, column_comment, column_type, column_is_partition)
    '''
    context = {
        'status': 1
    }
    return HttpResponse(json.dumps(context), mimetype='application/json')

@login_required()
def register_table(request):


    username = request.user.username
    table_info = json.loads(str(request.POST.get("table_info")))
    logger.info("user %s register table, info %s", username, table_info)

    name = table_info['name']
    uri = table_info['uri']
    department = table_info['department']
    service = table_info['service']
    service_supervisor = table_info['service_supervisor']
    supervisor = table_info['supervisor']
    description = table_info['description']
    privacy_level = table_info['privacy_level']
    grant_user_list = table_info['grant_user_list']
    deser_format = table_info['deser_format']
    definition = table_info['definition']
    data_type = table_info['data_type']

    update_time = table_info['update_interval'] if ('update_interval' in table_info) else 0
    table_id = table_info['id'] if ('id' in table_info) else None
    log_hold_time = table_info['log_preserve_time'] if ('log_preserve_time' in table_info) else -1
    #change uri
    if 'log-data' == data_type:
        uri = settings.LOG_TABLE_HDFS_PATH_PREFIX+uri
        #update_time = 0
    '''
    result, error_msg = check_valid(name, uri, definition)
    if result is not True:
        context = {
            'status': 1,
            'error_msg': error_msg
        }
        logger.info('error:%s', error_msg)
        return HttpResponse(json.dumps(context), mimetype='application/json')
    '''
    if not table_id:
        # create a new table_log
        table = ExistedTable(
            name=name,
            uri=uri,
            department=department,
            service=service,
            service_supervisor=service_supervisor,
            supervisor=supervisor,
            description=description,
            privacy_level=privacy_level,
            grant_user_list=grant_user_list,
            deser_format=deser_format,
            definition=definition,
            created_by=username,
            created_time=timezone.now(),
            modify_by=username,
            modify_time=timezone.now(),
            update_time=update_time,
            data_type=data_type,
            log_hold_time=log_hold_time
        )
    else:
        #edit old table_log
        table = ExistedTable.objects.get(id=table_id)
        table.name = name
        table.uri = uri
        table.department = department
        table.service = service
        table.service_supervisor = service_supervisor
        table.supervisor = supervisor
        table.description = description
        table.privacy_level = privacy_level
        table.grant_user_list = grant_user_list
        table.deser_format = deser_format
        table.definition = definition
        table.modify_by = username
        table.modify_time = timezone.now()
        table.data_type = data_type
        table.update_time = update_time
        table.log_hold_time = log_hold_time
    #save or update
    table.save()
    logger.info("operation existed table successfully, id %s", table_id)
    #send mail
    table_url = request.get_host()+'/static/data-platform-fe/dist/#/log-table/'+str(table.id)
    logger.info("path: %s", table_url)
    send_mail(table_url, username, '存量日志数据表操作', settings.LOG_TABLE_CHECK_EMAIL)

    context = {
        'status': 1,
        'table_info': {
            'id': table.id
        }
    }

    return HttpResponse(json.dumps(context), mimetype='application/json')


def describe_table(request):
    table_id = int(request.GET.get("table_id"))
    logger.debug("enter describe table, id %s", table_id)
    operator = HiveTableOperator()
    table_info = operator.describe_table(table_id)
    '''
    table_info = {
        'service_name': '黄页',
        'name': 'access',
        'comment': 'web api',
        'columns': [
            {'tag': 'XXX',
             'name': 'api',
             'comment': 'api_comment',
             'type': 'string',
             'is_partition': False},
            {'tag': 'XXX',
             'name': 'uuid',
             'comment': 'user id',
             'type': 'long',
             'is_partition': False},
            {'tag': 'XXX',
             'name': 'year',
             'comment': 'year_comment',
             'type': 'int',
             'is_partition': True}
        ]
    }
    '''
    context = {
        'status': 1,
        'table_info': table_info
    }
    return HttpResponse(json.dumps(context), mimetype='application/json')


def get_tables(request):
    logger.info("enter get tables")
    operator = HiveTableOperator()
    tables = operator.get_tables()
    '''
    tables = [
        {'service_id': 101,
         'service_name': '黄页',
         'table_id': 1101,
         'table_name': "click"},
        {'service_id': 102,
         'service_name': '小米生活',
         'table_id': 1102,
         'table_name': 'webview'},
    ]
    '''
    context = {
        'status': 1,
        'tables': tables
    }
    return HttpResponse(json.dumps(context), mimetype='application/json')


@login_required()
def file_browser_list(request):
    try:
        username = request.user.username
        path = request.GET.get("path")
        webhdfs = WebHdfs()
        list_res = webhdfs.listdir_stats(path)
        items = []
        for item in list_res:
            item_name = item.name
            # item_path = item.path
            item_type = item.type
            items.append({
                'name': item_name,
                'type': item_type
            })
        context = {
            'status': 1,
            'data': items
        }
        return HttpResponse(json.dumps(context), mimetype='application/json')
    except WebHdfsException, e:
        traceback.print_exc()
        context = {
            'status': -1,
            'message': 'permission denied'
        }
        logger.error("permission denied to access path %s for user %s, exception %s", path, username, e)
        return HttpResponse(json.dumps(context), mimetype='application/json')


WEBHDFS_READ_MAX_TIMES = 100
WEBHDFS_READ_LENGTH_PER_TIME = 10000
WEBHDFS_READ_MAX_LINES = 1000

@login_required()
def file_preview(request):
    username = request.user.username
    path = request.GET.get("path")
    file_format = request.GET.get("file_format")
    column_delimiter = unescape(request.GET.get("column_delimiter"))

    read_time = 0
    webhdfs = WebHdfs()
    list_status = webhdfs.listdir_stats(path)
    files_in_folder = []
    for item in list_status:
        if item['type'] == 'FILE':
            files_in_folder.append(path + item['pathSuffix'])
            break
    if len(files_in_folder) <= 0:
        context = {
            'status': 1,
            'content': ''
        }
        return HttpResponse(json.dumps(context), mimetype='application/json')

    res_lines = []
    content_last = ""
    file_index = 0
    read_offset = 0
    while read_time < WEBHDFS_READ_MAX_TIMES:
        content = webhdfs.read(files_in_folder[file_index], read_offset, WEBHDFS_READ_LENGTH_PER_TIME)
        read_offset += len(content)
        content = content_last + content
        if len(content.strip()) <= 0:
            file_index += 1
            if file_index >= len(files_in_folder):
                break

        lines = content.split("\n")
        line_len = len(lines)
        line_no = 0
        for line in lines:
            if line_no < line_len - 1:
                res_lines.append(line)
            if len(res_lines) >= WEBHDFS_READ_MAX_LINES:
                break
            line_no += 1
        content_last = lines[line_len - 1]
        read_time += 1

    # parse content table
    table_json = decode_lines(lines, column_delimiter)

    context = {
        'status': 1,
        'table_data': json.dumps(table_json)
    }
    return HttpResponse(json.dumps(context), mimetype='application/json')


def unescape(value):
    if value == "\\t":
        return "\t"
    else:
        return value


def decode_file(file_path, file_format):
    return []


def decode_lines(lines, column_delimiter):
    head = []
    body = []

    if column_delimiter == "json":
        head = list()
        for line in lines:
            if not line or line == "":
                continue

            # construct table head
            line_json = json.loads(line)
            line_keys = line_json.keys()
            line_keys.extend(head)
            head = list(set(line_keys))

            body.append(line_json)
    elif column_delimiter == "\t" or column_delimiter == " ":
        column_num_max = 0
        for line in lines:
            columns = line.split(column_delimiter)
            if len(columns) > column_num_max:
                column_num_max = len(columns)
            body.append(dict([("c" + str(x), columns[x]) for x in xrange(0, len(columns))]))
        for x in xrange(0, column_num_max):
            head.append("c" + str(x))

    return {"head": head, "body": body}

@login_required()
def log_table_list(request):
    tables = ExistedTable.objects.all()

    logger.info("show existed table successfully")

    context = dict()
    context['status'] = 1
    context['table_info_list'] = []

    for table in tables:
        tmp = dict()
        tmp['id'] = table.id
        tmp['name'] = table.name
        tmp['service'] = table.service
        tmp['department'] = table.department
        # service
        tmp['service_supervisor'] = table.service_supervisor
        # log supervisor
        tmp['supervisor'] = table.supervisor
        # description
        tmp['description'] = table.description
        # list of table
        context['table_info_list'].append(tmp)

    logger.info("get existed table successfully")

    return HttpResponse(json.dumps(context), mimetype='application/json')

@login_required()
def log_table_info(request):
    table_id = request.GET.get('table_id')
    table_id = int(table_id)
    table = ExistedTable.objects.get(id=table_id)

    context = dict()
    context['status'] = 1
    uri = table.uri
    if settings.LOG_TABLE_HDFS_PATH_PREFIX in uri:
        #uri for log-data
        uri = uri.split(settings.LOG_TABLE_HDFS_PATH_PREFIX)[1]

    table_info = dict()
    table_info['id'] = table_id
    table_info['name'] = table.name
    table_info['uri'] = uri
    table_info['department'] = table.department
    table_info['service'] = table.service
    table_info['service_supervisor'] = table.service_supervisor
    table_info['supervisor'] = table.supervisor
    table_info['description'] = table.description
    table_info['privacy_level'] = table.privacy_level
    table_info['grant_user_list'] = table.grant_user_list
    table_info['deser_format'] = table.deser_format
    table_info['definition'] = table.definition
    table_info['data_type'] = table.data_type
    table_info['update_interval'] = table.update_time
    # todo －1 代表 中间数据
    table_info['log_preserve_time'] = table.log_hold_time

    context['table_info'] = table_info

    return HttpResponse(json.dumps(context), mimetype='application/json')


def send_mail(table_url, user, title, email='wangzihao@xiaomi.com'):
    httpclient = None
    host = 'support.d.xiaomi.net'
    body = 'hello!<br>'
    body += user+' does something to a table!<br>'
    body += 'information url:<a href="http://'+table_url+'">表链接</a>'

    try:
        params = urllib.urlencode({'title': title, 'body': body,
                                   'address': email, 'mailFrom': 'noreply@miliao.com',
                                   'locale': ''})
        headers = {"Content-type": "application/x-www-form-urlencoded;charset=utf8"}

        httpclient = httplib.HTTPConnection(host, 80, timeout=30)
        httpclient.request("POST", "/mail/send", params, headers)

        response = httpclient.getresponse()
        code = response.status
        if 200 == code:
            logger.info("send a mail to %s", email)
            logger.info("description : %s", response.read())
        else:
            logger.info("code: %d", code)
    except Exception, e:
        print e
    finally:
        if httpclient:
            httpclient.close()


def check_valid(name, uri, description):
    result = True
    error_message = '日志名与路径已经存在！\n'
    if '/' not in name:
        result = False
        error_message = '日志名不合法!\n'
        return result, error_message
    try:
        table = ExistedTable.objects.get(name=name, uri=uri)
        result = False
    except ExistedTable.DoesNotExist:
        logger.info("log not exit!")
        '''
        error_code, error_message = check_thrift.check_thrift(name, description)
        if 0 != error_code:
            result = False
        '''
    return result, error_message