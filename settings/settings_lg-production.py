from .base import *

MANAGERS = ADMINS

TEMPLATE_DEBUG = DEBUG = True

MYSQL_SOCK = '10.101.10.158'
MYSQL_USER = 'collie'
MYSQL_PWD = 'collie'
MYSQL_PORT = '3306'

COLLIEXE_HOST = '10.101.10.158'
COLLIEXE_PORT = '8089'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'collie',
        'USER': MYSQL_USER,
        'PASSWORD': MYSQL_PWD,
        'HOST': MYSQL_SOCK,
        'PORT': MYSQL_PORT
    }
}

# EMAIL
EMAIL_BASE_URL = 'collie.pt.xiaomi.com'

# yarn clusters
YARN_CLUSTERS = "lgprc-xiaomi,lgprc-xiaomi2,azsgsrv-xiaomi,lgprc-xiaomi-preview"

# webhdfs
WEBHDFS_URL_1 = "http://10.2.201.18:11201/webhdfs/v1"
WEBHDFS_URL_2 = "http://10.2.201.14:11201/webhdfs/v1"
WEBHDFS_USERNAME = "h_sns"
WEBHDFS_DOAS = "h_sns"
WEBHDFS_SUPERUSER = "h_sns"

# module hdfs info
MODULE_HDFS_ROOT = "/user/" + WEBHDFS_DOAS + "/collie/modules/"
PROJECT_HDFS_ROOT = "/user/" + WEBHDFS_DOAS + "/collie/projects/"
 
# cas info
CAS_SERVER_URL = "https://cas.mioffice.cn"
CAS_AUTO_CREATE_USERS = True
