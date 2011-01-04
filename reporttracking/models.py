from django.db import models
from mutualtracker.fundtracking.models import Fund

class Country(models.Model):
    class Meta:
        verbose_name_plural = 'countries'
    name = models.CharField(max_length=255)
    def __unicode__(self):
        return self.name

class Industry(models.Model):
    class Meta:
        verbose_name_plural = 'industries'
    name = models.CharField(max_length=255)
    def __unicode__(self):
        return self.name

class Company(models.Model):
    class Meta:
        verbose_name_plural = 'companies'
    name = models.CharField(max_length=255)
    country = models.ForeignKey(Country)
    code = models.SmallIntegerField(null=True)
    ticker = models.CharField(max_length=15, null=True)
    industries = models.ManyToManyField(Industry)
    def __unicode__(self):
        return self.name

REPORT_TYPE_CHOICES = (
    (0, 'Invalid'),
    (1, 'Annual'),
    (2, 'Interim'),
)
REPORT_STATE_CHOICES = (
    (0, 'Null'),
    (1, 'Downloaded'),
    (2, 'Parsed'),
)
DEFAULT_UPLOAD_DIR = 'Reports'
class Report(models.Model):
    fund = models.ForeignKey(Fund)
    date = models.DateField()
    type = models.SmallIntegerField(choices=REPORT_TYPE_CHOICES)
    file_name = models.FileField(upload_to=DEFAULT_UPLOAD_DIR, max_length=255)
    state = models.SmallIntegerField(choices=REPORT_STATE_CHOICES)
    holdings = models.ManyToManyField(Company, through='Holding')
    def __unicode__(self):
        return '{0} - {1}: {2}'.format(self.fund, self.date, self.file_name)

class Holding(models.Model):
    report = models.ForeignKey(Report)
    company = models.ForeignKey(Company)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    percentage_of_nav = models.DecimalField(max_digits=10, decimal_places=2)
    def __unicode__(self):
        return '{0} - {1}'.format(self.report, self.company)
