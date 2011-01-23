from django.db import models
from datetime import timedelta

class Fund(models.Model):
    class Meta:
        db_table = 'funds'
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    def __unicode__(self):
        return self.name

    @property
    def latest_price(self):
        try:
            return self.price_set.all()[0]
        except IndexError:
            return {}

    @property
    def latest_15_day_price_set(self):
        try:
            return self.price_set.all()[:15]
        except IndexError:
            return Price.objects.none()

    def get_last_52_week_price_set_until(self, until_date):
        from_date = until_date - timedelta(52*7)
        return self.price_set.filter(date__gt=from_date)

    def get_last_52_week_min_max_price_until(self, until_date):
        return self.get_last_52_week_price_set_until(until_date).aggregate(models.Min('nav'), models.Max('nav'))

class Price(models.Model):
    class Meta:
        db_table = 'prices'
        ordering = ['-date']
    fund = models.ForeignKey(Fund)
    date = models.DateField()
    nav = models.DecimalField(max_digits=5, decimal_places=4)
    def __unicode__(self):
        return '{0} - {1}: {2}'.format(self.fund, self.date, self.nav)

