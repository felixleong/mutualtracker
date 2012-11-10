from mutualtracker.settings.base import *
from mutualtracker.settings import base

DEBUG = True
TEMPLATE_DEBUG = DEBUG

MIDDLEWARE_CLASSES = base.MIDDLEWARE_CLASSES + (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INSTALLED_APPS = base.INSTALLED_APPS + (
    'debug_toolbar',
    'django_extensions',
    'devserver',
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

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': True
}

DEVSERVER_MODULES = (
#    'devserver.modules.sql.SQLRealTimeModule',
#    'devserver.modules.sql.SQLSummaryModule',
#    'devserver.modules.profile.ProfileSummaryModule',

    # Modules not enabled by default
#    'devserver.modules.ajax.AjaxDumpModule',
#    'devserver.modules.profile.MemoryUseModule',
#    'devserver.modules.cache.CacheSummaryModule',
#    'devserver.modules.profile.LineProfilerModule',
)
