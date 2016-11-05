import json
import logging
from pyhs2.connections import Connection


logger = logging.getLogger("collie")


class HiveClient:
    def __init__(self, proxy_user="h_sns@XIAOMI.HADOOP", host="lg-hadoop-hive01.bj", port=9600,
                 user="h_sns@XIAOMI.HADOOP"):
        conf = dict()
        conf['krb_host'] = 'hadoop'
        conf['krb_service'] = 'hive_prc'
        conf['hive.server2.proxy.user'] = proxy_user
        conn = Connection(host=host,
                          port=port,
                          authMechanism="KERBEROS",
                          user=user,
                          password='',
                          database='default',
                          configuration=conf)
        self.client = conn.cursor()

    def create_database(self, database_name):
        try:
            self.client.execute("create database if not exists %s" % database_name)
            return self.client.getSchema()
        except Exception as e:
            logger.error("hit exception %s when create database %s", e, database_name)
            raise e

    def drop_database(self, database_name):
        try:
            self.client.execute("drop database %s" % database_name)
            return self.client.getSchema()
        except Exception as e:
            logger.error("hit exception %s when create database %s", e, database_name)
            raise e

    def show_databases(self):
        return self.client.getDatabases()

    def show_tables(self, database):
        self.client.execute("use %s" % database)
        self.client.execute("show tables")
        return self.client.fetch()

    def describe_table(self, database, table):
        self.client.execute("use %s" % database)
        self.client.execute("describe %s" % table)
        return self.client.fetch()

    def describe_formatted_table(self, extends_jar_path, custom_jar_path, database, table):
        self.client.execute("add jar {0}".format(extends_jar_path))
        self.client.execute("add jar {0}".format(custom_jar_path))
        self.client.execute("use %s" % database)
        self.client.execute("describe formatted %s.%s" % (database, table))
        return self.client.fetch()

    ## comment is Base64 encoded
    def create_xlog_table(self, database, extends_jar_path, custom_jar_path, table,
                          comment, partition_columns, ser_class, file_location):
        self.client.execute("use {0}".format(database))  # database name: test
        # jar path: /home/work/app/hive/lgprc-xiaomi13/extends/hive-extends-0.0.1-SNAPSHOT.jar
        self.client.execute("add jar {0}".format(extends_jar_path))
        # jar path: /home/work/app/hive/lgprc-xiaomi13/extends/collie-table-0.1.13.jar
        self.client.execute("add jar {0}".format(custom_jar_path))
        self.client.execute("drop table if exists {0}".format(table))
        execute_statement = ("create external table {0} "
                             + "comment \"{1}\" "
                             + "partitioned by ({2}) "
                             + "row format serde \"com.miliao.hive.extend.serde.ThriftBase64Deserializer\" "
                             + "with serdeproperties ( "
                             + "\"serialization.class\"=\"{3}\", "
                             + "\"serialization.format\"=\"org.apache.thrift.protocol.TBinaryProtocol\") "
                             + "stored as sequencefile location \"{4}\" ")\
            .format(table, comment, partition_columns, ser_class, file_location)
        logger.debug("table create statement: %s", execute_statement)
        self.client.execute(execute_statement)
        self.client.execute("MSCK REPAIR TABLE {0}".format(table))
        return True

if __name__ == "__main__":
    hive_client = HiveClient(proxy_user="h_wenghaibin")

    print ">> show databases"
    print hive_client.show_databases()

    print ">> create database"
    print hive_client.create_database("test")

    # print ">> drop database"
    # print hive_client.drop_database("test")

    database_name = "test"
    table_name = "music_search"

    print ">> create table"
    print hive_client.create_xlog_table("test",
                                        "/home/work/app/hive/lgprc-xiaomi13/extends/hive-extends-0.0.1-SNAPSHOT.jar",
                                        "/home/work/app/hive/lgprc-xiaomi13/extends/collie-table-0.1.13.jar",
                                        "music_search",
                                        "eyJzZXJ2aWNlX25hbWUiOiAibWlzZWFyY2giLCAibmFtZSI6ICJtdXNpY19zZWFyY2giLCAiY29sdW1ucyI6IFt7ImNvbW1lbnQiOiAidXNlciBpZCIsICJ0YWciOiAiWFhYIiwgInR5cGUiOiAiYmlnaW50IiwgIm5hbWUiOiAidXNlcmlkIn0sIHsiY29tbWVudCI6ICJ1c2VyIGFwaSAxNDE2MjA3NzkxLjE3IiwgInRhZyI6ICJYWFgiLCAidHlwZSI6ICJzdHJpbmciLCAibmFtZSI6ICJhcGl0eXBlIn0sIHsiY29tbWVudCI6ICJ1c2VyIHF1ZXJ5IiwgInRhZyI6ICJYWFgiLCAidHlwZSI6ICJzdHJpbmciLCAibmFtZSI6ICJxdWVyeSJ9XX0=",
                                        "year smallint, month tinyint, day tinyint",
                                        "com.xiaomi.common.logger.thrift.misearch.MusicSearchQueryLogEntry",
                                        "/user/h_scribe/miliao_legacy/misearch_musicsearchquerylogentry")

    print ">> show tables"
    print hive_client.show_tables("test")