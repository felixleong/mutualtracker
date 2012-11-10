from mutualtracker.reporttracking.models import Report, Company, Industry, Country, Holding
from django.contrib import admin

class HoldingInline(admin.TabularInline):
    model = Holding
    extra = 0

class ReportAdmin(admin.ModelAdmin):
    list_display = ('fund', 'date', 'type', 'state',)
    list_filter = ('date', 'type',)
    search_fields = ('fund__code', 'fund__name',)
    inlines = (HoldingInline,)

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', )
    list_filter = ('country', )
    search_fields = ('name', )

# Add the admin modules
admin.site.register(Report, ReportAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Industry)
admin.site.register(Country)
