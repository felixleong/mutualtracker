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

