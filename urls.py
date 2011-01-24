from django.conf.urls.defaults import handler404, include, patterns, url
from django.contrib.sitemaps import FlatPageSitemap
from django.conf import settings
from mutualtracker.fundtracking.sitemaps import FundSitemap
from mutualtracker.sitemaps import ViewsSitemap

# Enable the admin site
from django.contrib import admin
admin.autodiscover()

handler404 # Dummy, just to keep pylint happy :)
handler500 = 'mutualtracker.views.server_error'

sitemaps = {
    'flatpages': FlatPageSitemap,
    'funds': FundSitemap,
    'views': ViewsSitemap(
        (
            'mutualtracker.fundtracking.views.index',
        ),
        priority=1.0, changefreq='daily'
    ),
}

urlpatterns = patterns('',
    url(r'^$', 'mutualtracker.fundtracking.views.index', name='root'),
    (r'^funds/', include('mutualtracker.fundtracking.urls')),
    (r'^api/', include('mutualtracker.api.urls')),
    (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),

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
