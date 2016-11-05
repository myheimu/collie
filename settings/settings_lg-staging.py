from .base import *

MANAGERS = ADMINS

TEMPLATE_DEBUG = DEBUG = True

MYSQL_SOCK = 'localhost'
MYSQL_USER = 'collie'
MYSQL_PWD = 'collie'
MYSQL_PORT = '3306'

COLLIEXE_HOST = 'localhost'
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

# webhdfs
WEBHDFS_URL_1 = "http://10.2.201.14:11201/webhdfs/v1"
WEBHDFS_URL_2 = "http://10.2.201.18:11201/webhdfs/v1"
WEBHDFS_USERNAME = "hue"
WEBHDFS_DOAS = "h_sns"
WEBHDFS_SUPERUSER = "hue"

# module hdfs info
MODULE_HDFS_ROOT = "/user/" + WEBHDFS_DOAS + "/collie_staging/modules/"
PROJECT_HDFS_ROOT = "/user/" + WEBHDFS_DOAS + "/collie_staging/projects/"
