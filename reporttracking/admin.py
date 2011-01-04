from mutualtracker.reporttracking.models import Report, Company, Industry, Country
from django.contrib import admin

# Add the admin modules
admin.site.register(Report)
admin.site.register(Company)
admin.site.register(Industry)
admin.site.register(Country)
