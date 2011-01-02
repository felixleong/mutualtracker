from django.conf.urls.defaults import *
from django.conf import settings

# Enable the admin site
from django.contrib import admin
admin.autodiscover()

handler500 = 'mutualtracker.views.server_error'

urlpatterns = patterns('',
    url(r'^$', 'mutualtracker.fundtracking.views.index', name='root'),
    (r'^funds/', include('mutualtracker.fundtracking.urls')),
    (r'^api/', include('mutualtracker.api.urls')),

    # Admin site
    (r'^admin/', include(admin.site.urls)),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
)

# DEBUG: Settings that are only to be used in development environments
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        (r'^500/', 'mutualtracker.views.server_error'),
    )
