import os
from pyhs2.connections import Connection
__author__ = 'haibin'

if __name__ == "__main__":
    os.environ["KRB5_CONFIG"] = "/home/haibin/git/infra/hue/desktop/conf/krb5.conf"
    '''
    conn = Connection(host="lg-hadoop-hive01.bj",
                      port="9600",
                      user="h_wenghaibin@XIAOMI.HADOOP",
                      password="RI5KCvQQXHkZrm4hKeYB",
                      authMechanism="KERBEROS")
    '''


    '''
    conn = Connection(host="lg-ml-hadoop-hdp01.bj",
                      port="10000",
                      authMechanism="NOSASL")

    conn = Connection(host="lg-hadoop-hive01.bj",
                      port="9800",
                      authMechanism="NOSASL")
    '''
    conf = {} #server principal hive_prc/hadoop@XIAOMI.HADOOP
    conf['krb_host'] = 'hadoop'
    conf['krb_service'] = 'hive_prc'
    conf['hive.server2.proxy.user'] = 'h_wenghaibin'
    conn = Connection(host='lg-hadoop-hive01.bj',
                      port=9600,
                      authMechanism="KERBEROS",
                      user='h_sns@XIAOMI.HADOOP',
                      password='',
                      database='default',
                      configuration=conf)
    cur = conn.cursor()
    databases = cur.getDatabases()
    print databases
    print "%s" % "hello"