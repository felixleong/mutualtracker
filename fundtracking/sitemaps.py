from datetime import datetime
from django.contrib.sitemaps import Sitemap
from mutualtracker.fundtracking.models import Fund

class FundSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return Fund.objects.all()

    def lastmod(self, obj):
        latest_price = obj.latest_price

        if latest_price:
            return latest_price.date
        else:
            return datetime.now()
