from datetime import datetime
from django.shortcuts import get_object_or_404
from piston.handler import BaseHandler
from piston.utils import rc
from mutualtracker.fundtracking.models import Fund, Price

ISO8601_DATE_FORMAT='%Y-%m-%d'

class FundHandler(BaseHandler):
    """API handling class for funds"""
    model = Fund
    allowed_methods = ('GET',)
    fields = ('id', 'code', 'name',)

    def read(self, request, fund_id=None, fund_code=None):
        base = Fund.objects
        if fund_id:
            return base.get(pk=fund_id)
        elif fund_code:
            return base.get(code=fund_code)
        else:
            return base.all()

class PriceHandler(BaseHandler):
    model = Price
    allowed_methods = ('GET',)
    fields = ('id', 'date', 'nav', 'fund', )

    def read(self, request, action=None, fund_id=None, fund_code=None):
        if action == 'history':
            return self.history(request, fund_id, fund_code)
        else:
            return self.list()

    def list(self):
        return Price.objects.all()[:20]

    def history(self, request, fund_id=None, fund_code=None):
        # GET parameters
        since_str = request.GET.get('since', '')
        until_str = request.GET.get('until', '')
        count_str = request.GET.get('count', 20)

        # Parse the input parameters
        try:
            if since_str:
                since = datetime.strptime(since_str, ISO8601_DATE_FORMAT)
            else:
                since = None

            if until_str:
                until = datetime.strptime(until_str, ISO8601_DATE_FORMAT)
            else:
                until = None

            count = int(count_str)
            if count > 200:
                count = 200
        except ValueError, e:
            resp = rc.BAD_REQUEST
            resp.write(e)
            return resp

        # Retrieve the fund details
        if fund_id:
            fund = get_object_or_404(Fund, pk=fund_id)
            base = fund.price_set
        elif fund_code:
            fund = get_object_or_404(Fund, code=code)
            base = fund.price_set

        # Add the filters when necessary
        if since:
            base = base.filter(date__gte=since)
        if until:
            base = base.filter(date__lte=until)

        # Return the data to the user
        return base.all()[:count]

