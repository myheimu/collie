from .base import *

MANAGERS = ADMINS

TEMPLATE_DEBUG = DEBUG = True

UPLOAD_MODE = 'git_only'

MYSQL_SOCK = '10.108.60.53'
MYSQL_USER = 'collie'
MYSQL_PWD = 'collie'
MYSQL_PORT = '3306'

COLLIEXE_HOST = '10.108.43.40'
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

# yarn clusters
YARN_CLUSTERS = "c3prc-micloud,lgprc-xiaomi,lgprc-xiaomi2,c3prc-micloud-debug"

# EMAIL
EMAIL_BASE_URL = 'collie.micloud.xiaomi.net'

# webhdfs
WEBHDFS_URL_1 = "http://10.2.201.18:11201/webhdfs/v1"
WEBHDFS_URL_2 = "http://10.2.201.14:11201/webhdfs/v1"
WEBHDFS_USERNAME = "h_micloud_collie"
WEBHDFS_DOAS = "h_micloud_collie"
WEBHDFS_SUPERUSER = "h_micloud_collie"

# module hdfs info
MODULE_HDFS_ROOT = "/user/" + WEBHDFS_DOAS + "/collie/modules/"
PROJECT_HDFS_ROOT = "/user/" + WEBHDFS_DOAS + "/collie/projects/"

# cas info
CAS_SERVER_URL = "https://cas.mioffice.cn"
CAS_AUTO_CREATE_USERS = True
