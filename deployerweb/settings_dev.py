"""
Django settings for deployerweb project.

Generated by 'django-admin startproject' using Django 1.8.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
ROOT_PATH = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
# Relative pass from current directory, just during development to allow run it from any location
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

# TODO: Should be removed before final merge
ROOT_PATH = '/Users/yflerko/git/eBay/'
BASE_DIR = ROOT_PATH + '/web2_deployer'
PROJECT_ROOT = BASE_DIR
SITE_ROOT = ROOT_PATH + '/web2_deployer/deployerweb'


DB_LOCATION = BASE_DIR + '/mp-db/'

LOG_DIR = BASE_DIR + '/logs/'

# Directories Related to Deployment
# Configuration files location
DEPLOYER_CFGS = BASE_DIR + '/mp-conf/'
DEPLOYER_TARS = BASE_DIR + '/mp-tars/'

# Remove after development :)
print BASE_DIR
print PROJECT_ROOT
print ROOT_PATH
print SITE_ROOT

ENV_DEV = True

# Websocket buffer size
WS_BUFFER_SIZE = 4

# The ID, as an integer, of the current site in the django_site database table.
SITE_ID = 1

# Absolute filesystem path to the directory that will hold user-uploaded files.
# https://docs.djangoproject.com/en/1.8/ref/settings/#media-root
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# https://docs.djangoproject.com/en/1.8/ref/settings/#media-url
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# https://docs.djangoproject.com/en/1.8/ref/settings/#static-root
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = SITE_ROOT + '/static/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/ref/settings/#static-url
STATIC_URL = '/static/'

# ADMIN_MEDIA_PREFIX depricated since 1.4 and Django
# will now expect to find the admin static files under the URL <STATIC_URL>/admin/.
# https://docs.djangoproject.com/en/1.8/releases/1.4/#django-contrib-admin

# Additional locations of static files
# https://docs.djangoproject.com/en/1.8/ref/settings/#staticfiles-dirs
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
# https://docs.djangoproject.com/en/1.8/ref/settings/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'm8$@8)h&$65-zpaas)r#m*$52zn)eeycw!4zvynl-gd%zy&mju'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)


# Application definition

LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'deployerweb.urls'

# Sessions
# https://docs.djangoproject.com/en/1.8/topics/http/sessions/#configuring-sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Templates configuration, new style since Django 1.8
# https://docs.djangoproject.com/en/1.8/ref/settings/#templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            '{}/templates'.format(SITE_ROOT)
        ],
        'APP_DIRS': False,
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Since we run Django thru Tornado we wont specify this parameter.
# https://docs.djangoproject.com/en/1.8/ref/settings/#wsgi-application
# WSGI_APPLICATION = 'deployerweb.wsgi.application'
WSGI_APPLICATION = None


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(DB_LOCATION, 'WebDeployerDev.sqlite3'),
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Amsterdam'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# LOGGING
# https://docs.djangoproject.com/en/1.8/ref/settings/#logging
# https://docs.djangoproject.com/en/1.8/topics/logging/#configuring-logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
