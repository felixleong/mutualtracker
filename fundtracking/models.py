from django.db import models
from django.db.models import Max, Min
from datetime import timedelta

class Fund(models.Model):
    class Meta:
        db_table = 'funds'
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    def __unicode__(self):
        return self.name

    @property
    def current_day_price(self):
        price_set = self.price_set.all()
        if price_set:
            return price_set[0]
        else:
            return None

    @property
    def previous_day_price(self):
        price_set = self.price_set.all()
        if price_set and price_set.count() >= 2:
            return price_set[1]
        else:
            return None

    @property
    def latest_15_day_price_set(self):
        price_set = self.price_set.all()
        if price_set:
            return price_set[:15]
        else:
            return []

    @property
    def last_52_week_price_set(self):
        try:
            self._last_52_week_price_set
        except AttributeError:
            current_day_price = self.current_day_price
            if current_day_price:
                until_date = current_day_price.date
                from_date = until_date - timedelta(52*7)
                self._last_52_week_price_set = self.price_set.filter(date__gt=from_date, date__lte=until_date)
            else:
                self._last_52_week_price_set = []

        return self._last_52_week_price_set

    @property
    def last_52_week_ceiling_price(self):
        if self.last_52_week_price_set:
            return self.last_52_week_price_set.aggregate(Max('nav'))['nav__max']
        else:
            return 0.0000

    @property
    def last_52_week_floor_price(self):
        if self.last_52_week_price_set:
            return self.last_52_week_price_set.aggregate(Min('nav'))['nav__min']
        else:
            return 0.0000


class Price(models.Model):
    class Meta:
        db_table = 'prices'
        ordering = ['-date']
    fund = models.ForeignKey(Fund)
    date = models.DateField()
    nav = models.DecimalField(max_digits=5, decimal_places=4)
    def __unicode__(self):
        return '{0} - {1}: {2}'.format(self.fund, self.date, self.nav)

class Country(models.Model):
    class Meta:
        db_table = 'countries'
        verbose_name_plural = 'countries'
    name = models.CharField(max_length=255)
    def __unicode__(self):
        return self.name

class Industry(models.Model):
    class Meta:
        db_table = 'industries'
        verbose_name_plural = 'industries'
    name = models.CharField(max_length=255)
    def __unicode__(self):
        return self.name

class Company(models.Model):
    class Meta:
        db_table = 'companies'
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
    class Meta:
        db_table = 'reports'
    fund = models.ForeignKey(Fund)
    date = models.DateField()
    type = models.SmallIntegerField(choices=REPORT_TYPE_CHOICES)
    file_name = models.FileField(upload_to=DEFAULT_UPLOAD_DIR, max_length=255)
    state = models.SmallIntegerField(choices=REPORT_STATE_CHOICES)
    holdings = models.ManyToManyField(Company, through='Holding')
    def __unicode__(self):
        return '{0} - {1}: {2}'.format(self.fund, self.date, self.file_name)

class Holding(models.Model):
    class Meta:
        db_table = 'holdings'
    report = models.ForeignKey(Report)
    company = models.ForeignKey(Company)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    percentage_of_nav = models.DecimalField(max_digits=10, decimal_places=2)
    def __unicode__(self):
        return '{0} - {1}'.format(self.report, self.company)

