# Django settings for collie project.
import os
from os.path import expanduser

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
# ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# DB configuration.
MYSQL_SOCK = '127.0.0.1'
MYSQL_USER = 'collie'
MYSQL_PWD = 'collie'
MYSQL_PORT = '3306'

# EMAIL
EMAIL_HOST = 'mail.srv'
EMAIL_FROM = 'wu@appsmtp.xiaomi.com'
EMAIL_BASE_URL = 'localhost:8000'

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

# project  path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# base path
HOME_PATH = expanduser("~")
DATA_BASE = HOME_PATH + "/data/collie/"

# media location path
MEDIA_PATH = DATA_BASE + "media/"
if not os.path.exists(MEDIA_PATH):
    os.makedirs(MEDIA_PATH)

# git repository path
GIT_REPOSITORY_PATH = DATA_BASE + "repository/"
if not os.path.exists(GIT_REPOSITORY_PATH):
    os.makedirs(GIT_REPOSITORY_PATH)

# log location path
LOG_PATH = DATA_BASE + "log/"
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)

# the location to save project
PROJECT_SAVE_PATH = DATA_BASE + "project-save/"
if not os.path.exists(PROJECT_SAVE_PATH):
    os.makedirs(PROJECT_SAVE_PATH)

## collie table project path
# THRIFT_TABLE_PROJECT_PATH = DATA_BASE + "collie-table/"
# if not os.path.exists(THRIFT_TABLE_PROJECT_PATH):
#     print "Error: please setup THRIFT_TABLE_PROJECT_PATH content first, path %s" % THRIFT_TABLE_PROJECT_PATH
#     exit(-1)

# yarn clusters
YARN_CLUSTERS = "lgprc-xiaomi,lgprc-xiaomi2"

# remote hive server host
HIVE_SERVER_HOST = "10.2.201.167"
HIVE_SERVER_EXTENDS_PATH = "/home/work/app/hive/lgprc-xiaomi13/extends/"

# webhdfs
WEBHDFS_URL_1 = "http://10.2.201.14:11201/webhdfs/v1"
WEBHDFS_URL_2 = "http://10.2.201.18:11201/webhdfs/v1"
WEBHDFS_USERNAME = "h_sns"
WEBHDFS_DOAS = "h_sns"
WEBHDFS_SUPERUSER = "h_sns"

# module mode
REPOSITORY_SAVE_MODE_DB = "db"
REPOSITORY_SAVE_MODE_HDFS = "hdfs"
REPOSITORY_SAVE_MODE = REPOSITORY_SAVE_MODE_HDFS

# module hdfs info
MODULE_HDFS_ROOT = "/user/" + WEBHDFS_DOAS + "/collie_local/modules/"
PROJECT_HDFS_ROOT = "/user/" + WEBHDFS_DOAS + "/collie_local/projects/"

# how to upload file for module
# 'git_only' | 'local_only' | 'full'
UPLOAD_MODE = 'full'

# LOGIN_URL = '/accounts/login'
# LOGIN_REDIRECT_URL = '/project/index'

# DAFAULT PATH for log_table
LOG_TABLE_HDFS_PATH_PREFIX = '/user/h_scribe/'
# E-MAIL for someone check the operation of log_table
LOG_TABLE_CHECK_EMAIL = 'liangkun@xiaomi.com;wanggang1@xiaomi.com;wangzihao@xiaomi.com'

# authentication via cas
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_cas.backends.CASBackend',
    'object_permissions.backend.ObjectPermBackend'
)

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = MEDIA_PATH

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = MEDIA_PATH

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.abspath(os.path.curdir) + "/static/",
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'k!ke25*^vyo3nuxd-b^(iek4jati(7_&q#-xf*2-_4&d7tgaz5'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)
'''
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django_cas.middleware.CASMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
'''

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_cas.middleware.CASMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

CAS_SERVER_URL = "https://casdev.mioffice.cn"
CAS_AUTO_CREATE_USERS = True
# CAS_LOGOUT_COMPLETELY = True

ROOT_URLCONF = 'collie.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'collie.wsgi.application'

PROJECT_PATH = os.path.abspath(os.path.curdir)
TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
    os.path.join(PROJECT_PATH, 'module/templates'),
    os.path.join(PROJECT_PATH, 'project/templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django_cas',
#    'dajaxice',
#    'dajax',
    'core',
    'module',
    'project',
    'profiles',
    'table',
    'object_permissions',
    'south',
    'util'
)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'verbose': {
            'format': '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s : "%(message)s"'
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'collie_file_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': LOG_PATH + 'collie.log',
            'maxBytes': '1024',
            'backupCount': '10'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'collie': {
            'handlers': ['console', 'collie_file_handler'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django_cas.backends': {
            'handlers': ['console', 'collie_file_handler'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}
