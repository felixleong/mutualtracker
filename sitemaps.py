from datetime import datetime
import types
from django.core.urlresolvers import reverse
from django.contrib.sitemaps import Sitemap

class ViewsSitemap(Sitemap):
    views = []

    def __init__(self, views, priority=None, changefreq=None):
        if isinstance(views, (types.TupleType, types.ListType)):
            self.views = views
        self.priority = priority
        self.changefreq = changefreq

    def items(self):
        return self.views

    def location(self, obj):
        return reverse(obj)

    def lastmod(self, obj):
        return datetime.now()
