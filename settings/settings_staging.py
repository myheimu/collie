from .base import *

MANAGERS = ADMINS

TEMPLATE_DEBUG = DEBUG = True

MYSQL_SOCK = '10.99.168.41'
MYSQL_USER = 'collie'
MYSQL_PWD = 'collie'
MYSQL_PORT = '3306'

COLLIEXE_HOST = '127.0.0.1'
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
WEBHDFS_USERNAME = "h_sns"
WEBHDFS_DOAS = "h_sns"
WEBHDFS_SUPERUSER = "h_sns"

# module hdfs info
MODULE_HDFS_ROOT = "/user/" + WEBHDFS_DOAS + "/staging/modules/"
PROJECT_HDFS_ROOT = "/user/" + WEBHDFS_DOAS + "/staging/projects/"
