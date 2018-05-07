"""Settings for wagtailimporter tests"""
import os

INSTALLED_APPS = [
    'wagtailimporter',
    'tests.app',

    'taggit',
    'modelcluster',

    'wagtail.core',
    'wagtail.admin',
    'wagtail.users',
    'wagtail.sites',
    'wagtail.snippets',
    'wagtail.search',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.contrib.routable_page',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
]

ALLOWED_HOSTS = ['localhost']

SECRET_KEY = 'not a secret'

ROOT_URLCONF = 'tests.app.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('DATABASE_NAME', ':memory:'),
    },
}

WAGTAIL_SITE_NAME = 'Wagtail Importer'

DEBUG = True

USE_TZ = True
TIME_ZONE = 'Australia/Hobart'

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'wagtail.core.middleware.SiteMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages'
            ],
        },
    },
]

STATIC_ROOT = os.path.join(os.path.dirname(__file__), 'static')
STATIC_URL = '/static/'
