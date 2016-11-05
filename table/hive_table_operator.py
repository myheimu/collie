# -*- coding: UTF-8 -*-
import json
import base64
import commands
import logging
import subprocess
import time
from core.hive_client import HiveClient

from settings import settings
from table.models import Service, Table
from table.table_operator import TableOperator


logger = logging.getLogger("collie")


class HiveTableOperator(TableOperator):
    def __init__(self):
        self._hive_client = HiveClient()
        pass

    def create_table(self, table_info):
        # we cannot create table which is already exist
        # check the validation of each command before start to create table

        if 'service_name' not in table_info:
            service_id = int(table_info['service_id'])
            service = Service.objects.get(id=service_id)
            service_name = service.name
        else:
            service_name = table_info['service_name']
        table_name = table_info['name']

        # create table logger in git project
        thrift_file_content = self._construct_thrift_file_content(service_name, table_info)
        create_table_args = ["{0}/table/scripts/create_table.sh -p {1} -s {2} -t {3} -f '{4}'".format(
            settings.PROJECT_PATH, settings.THRIFT_TABLE_PROJECT_PATH, service_name, table_name, thrift_file_content
        )]
        create_table_process = subprocess.Popen(create_table_args, stdout=subprocess.PIPE, shell=True)
        while True:
            line = create_table_process.stdout.readline()
            if not line:
                break
            logger.info(line)
        create_table_process.wait()
        if create_table_process.returncode != 0:
            logger.error("table create failed, code " + str(create_table_process.returncode))
            return False
        else:
            logger.info("table create successfully")

        # get latest created logger version
        version = self._get_latest_git_tag()
        if not version:
            logger.error("get latest git tag failed")
            return False
        logger.info("thrift logger project version is %s ", version)

        # scp custom jar to remote machine
        custom_jar_scp_command = "scp {0}/target/collie-table-{1}.jar {2}:{3}".format(
            settings.THRIFT_TABLE_PROJECT_PATH, version, settings.HIVE_SERVER_HOST, settings.HIVE_SERVER_EXTENDS_PATH
        )
        (status, _) = commands.getstatusoutput(custom_jar_scp_command)
        if status != 0:
            logger.error("failed to copy custom jar file to remote hive server")
            return False
        logger.info("successfully copy custom jar file to remote hive server")

        # create hive table
        self._hive_client.create_xlog_table(
            "test",
            "{0}hive-extends-0.0.1-SNAPSHOT.jar".format(settings.HIVE_SERVER_EXTENDS_PATH),
            "{0}collie-table-{1}.jar".format(settings.HIVE_SERVER_EXTENDS_PATH, version),
            table_name,
            base64.b64encode(json.dumps(table_info)),
            "year smallint, month tinyint, day tinyint",  # TODO default
            "com.xiaomi.common.logger.thrift.{0}.{1}".format(service_name, table_name),
            "/user/h_scribe/miliao_legacy/misearch_musicsearchquerylogentry"  # TODO
        )

        # create hive in DB
        if 'service_name' not in table_info:
            service_id = int(table_info['service_id'])
            service = Service.objects.get(id=service_id)
            table = Table(name=table_name,
                          service=service)
            table.save()
            logger.info("successfully create table in db")

    @staticmethod
    def _construct_thrift_file_content(service_name, table_info):
        logger.info("construct thrift file content %s", table_info)

        # 1: optional i64 uuid; // tag: 1102, comment: user id
        field_optional_template = "{0}: {1} {2} {3}; // tag: {4}, comment: {5}"
        columns = table_info['columns']
        columns_content = ""
        column_index = 2
        for column in columns:
            column_tag = column['tag']
            column_name = column['name']
            column_type = column['type']
            column_comment = column['comment']
            file_content = field_optional_template.format(column_index, 'optional',
                                                          column_type, column_name, column_tag, column_comment)
            column_index += 1
            columns_content = columns_content + "\t" + file_content + "\n"
        table_name = table_info['name']
        table_comment = table_info['comment']

        content_template = """
namespace java com.xiaomi.common.logger.thrift.{0}

include "../common.thrift"

// table comment: {1}
struct {2} {{
\t1: required common.Common common;
{3}
}}
"""
        content = content_template.format(service_name, table_comment, table_name, columns_content)
        return content

    @staticmethod
    def get_tables():
        tables = Table.objects.all()
        tables_info = []
        for table in tables:
            tables_info.append({
                'service_id': table.service.id,
                'service_name': table.service.name,
                'table_id': table.id,
                'table_name': table.name
            })
        return tables_info

    def describe_table(self, table_id):
        table = Table.objects.get(id=table_id)
        # get latest created logger version
        version = self._get_latest_git_tag()
        if not version:
            logger.error("get latest git tag failed")
            return False
        logger.info("thrift logger project version is %s ", version)

        # how to get detail of table
        table_describe = self._hive_client.describe_formatted_table(
            "{0}hive-extends-0.0.1-SNAPSHOT.jar".format(settings.HIVE_SERVER_EXTENDS_PATH),
            "{0}collie-table-{1}.jar".format(settings.HIVE_SERVER_EXTENDS_PATH, version), "test", table.name)
        logger.info("table %s, comment %s", table.name, table_describe)
        table_info = self._get_comment(table_describe)
        service = table.service
        table_info["service_name"] = service.name
        logger.info("table %s, info %s", table.name, table_info)
        return table_info

    @staticmethod
    def _get_latest_git_tag():
        # get latest created logger version
        get_version_command = "cd {0}; git tag -l | sort -V | tail -1 | awk 'BEGIN {{ FS = \"-\" }} ; {{ print $3 }}'"
        (status, version) = commands.getstatusoutput(get_version_command.format(settings.THRIFT_TABLE_PROJECT_PATH))
        if status != 0:
            logger.error("failed to get latest version")
            return None
        logger.debug("thrift logger project version is %s ", version)
        return version

    @staticmethod
    def _get_comment(table_formatted_describe):
        for row in table_formatted_describe:
            logger.info(row[2])
            if row[0] == '' and row[1] and row[1].startswith('comment'):
                return json.loads(base64.b64decode(row[2]))
        return None

    @staticmethod
    # how test: Tools -> Run Django Console... (in PyCharm)
    #           >> from table.hive_table_operator import HiveTableOperator
    #           >> HiveTableOperator.test()
    def test():
    #if __name__ == "__main__":
        operator = HiveTableOperator()
        table_info = {
            'service_name': 'misearch',
            'name': 'music_search',
            'columns': [
                {
                    'tag': 'XXX',
                    'name': 'userid',
                    'type': 'bigint',
                    'comment': 'user id'},
                {
                    'tag': 'XXX',
                    'name': 'apitype',
                    'type': 'string',
                    'comment': 'user api ' + str(time.time())
                },
                {
                    'tag': 'XXX',
                    'name': 'query',
                    'type': 'string',
                    'comment': 'user query'
                }
            ]
        }
        logger.info(base64.b64encode(json.dumps(table_info)))
        operator.create_table(table_info)
        # operator.describe_table("music_search")
