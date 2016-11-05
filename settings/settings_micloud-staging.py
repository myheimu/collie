from .base import *

MANAGERS = ADMINS

TEMPLATE_DEBUG = DEBUG = True

MYSQL_SOCK = '10.99.168.156'
MYSQL_USER = 'collie'
MYSQL_PWD = 'collie'
MYSQL_PORT = '3306'

COLLIEXE_HOST = '10.99.168.155'
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
EMAIL_BASE_URL = 'staging.collie.micloud.xiaomi.net'

# webhdfs
WEBHDFS_URL_1 = "http://10.2.201.18:11201/webhdfs/v1"
WEBHDFS_URL_2 = "http://10.2.201.14:11201/webhdfs/v1"
WEBHDFS_USERNAME = "h_micloud_staging"
WEBHDFS_DOAS = "h_micloud_staging"
WEBHDFS_SUPERUSER = "h_micloud_staging"

# module mode
MODULE_SAVE_MODE_DB = "db"
MODULE_SAVE_MODE_HDFS = "hdfs"
MODULE_SAVE_MODE = MODULE_SAVE_MODE_HDFS

# module hdfs info
MODULE_HDFS_ROOT = "/user/" + WEBHDFS_DOAS + "/collie/modules/"
PROJECT_HDFS_ROOT = "/user/" + WEBHDFS_DOAS + "/collie/projects/"
