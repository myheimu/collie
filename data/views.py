import json
import urllib
import urllib2
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

__author__ = 'haibin'


@login_required()
def hello_world(request):
    context = {
        "data": "hello world"
    }
    return HttpResponse(json.dumps(context), mimetype='application/json')


@login_required()
def get_user_profile(request):
    user = request.user
    context = {
        "username": user.username
    }
    return HttpResponse(json.dumps(context), mimetype='application/json')


################ following apis dependency ######################
# xielong: lib or api to upload thrift to git & mvn package & mvn deploy
# peng.zhang: hive python api to visit hive server
##################################################################

################ action list #################
# fake each api data to fe for intrgration
# write each api's logic
##############################################

# @login_required()
def get_tables(request):
    # get tables from hive server using name prefix
    # each table presents with basic info
    return ""


# @login_required()
def operate_table(request):
    # get table columns
    # create thrift file content
    # push thrift to git & mvn package & return release version number
    # retrieve log store path
    # create hive table using table column definition and store path, ...

    return ""


# @login_required()
def describe_table(request):
    # get detail of table
    return ""