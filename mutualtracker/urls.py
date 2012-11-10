from django.conf.urls.defaults import handler404, include, patterns, url
from django.contrib.sitemaps import FlatPageSitemap
from django.conf import settings
from mutualtracker.fundtracking.sitemaps import FundSitemap
from mutualtracker.sitemaps import ViewsSitemap

# Enable the admin site
from django.contrib import admin
admin.autodiscover()

handler404  # Dummy, just to keep pylint happy :)
handler500 = 'mutualtracker.errors.server_error'

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

urlpatterns = patterns(
    '',
    url(r'^$', 'mutualtracker.fundtracking.views.index', name='home'),
    url(r'^funds/', include('mutualtracker.fundtracking.urls')),
    url(r'^api/', include('mutualtracker.api.urls')),
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap',
        {'sitemaps': sitemaps}),

    # Admin site
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Mezzaine - reserve for last
    url("^blog/", include("mezzanine.urls")),
)

# DEBUG: Settings that are only to be used in development environments
if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        url(r'^500/', 'mutualtracker.errors.server_error'),
    )
