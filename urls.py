from django.conf.urls.defaults import *
from django.conf import settings

# Enable the admin site
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^funds/', include('fundtracking.urls')),

    # Admin site
    (r'^admin/', include(admin.site.urls)),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
)

# DEBUG: Settings that are only to be used in development environments
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )
