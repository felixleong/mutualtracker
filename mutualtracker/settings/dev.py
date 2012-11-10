from mutualtracker.settings.base import *
from mutualtracker.settings import base

DEBUG = True
TEMPLATE_DEBUG = DEBUG

MIDDLEWARE_CLASSES = base.MIDDLEWARE_CLASSES + (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INSTALLED_APPS = base.INSTALLED_APPS + (
    'debug_toolbar',
)

INTERNAL_IPS = (
    '192.168.0.*',
    '127.0.0.1',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
