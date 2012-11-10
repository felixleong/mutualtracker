'''
File: views.py
Author: Seh Hui "Felix" Leong
Description: Views for fund tracking page
'''
from datetime import timedelta
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from mutualtracker.fundtracking.models import Fund

def index(request):
    """Retrieve a fund listing"""
    fund_list = Fund.objects.order_by('code')
    for fund in fund_list:
        latest_price = fund.latest_price
        if latest_price:
            fund.latest_update = latest_price.date
            fund.latest_nav = latest_price.nav
            min_max = fund.get_last_52_week_min_max_price_until(fund.latest_update)
            fund.min_nav = min_max['nav__min']
            fund.max_nav = min_max['nav__max']
    return render_to_response('fundtracking/index.html', {'fund_list': fund_list}, context_instance = RequestContext(request))

def view(request, fund_id=None, code=None):
    """Get a detailed view of the requested fund"""
    if fund_id:
        fund = get_object_or_404(Fund, pk=fund_id)
    else:
        fund = get_object_or_404(Fund, code=code)

    fund.last_5_day_price_set = fund.price_set.all()[0:5]
    if fund.last_5_day_price_set.count() < 2:
        # If we encountered a fund with no price listing yet, show a placeholder page
        return render_to_response('fundtracking/view_empty.html', {'fund': fund}, context_instance = RequestContext(request))

    fund.current_price = fund.last_5_day_price_set[0]
    fund.previous_price = fund.last_5_day_price_set[1]
    fund.price_difference = fund.current_price.nav - fund.previous_price.nav
    fund.price_difference_percentage = fund.price_difference / fund.previous_price.nav * 100

    min_max = fund.get_last_52_week_min_max_price_until(fund.current_price.date)
    fund.min_nav = min_max['nav__min']
    fund.max_nav = min_max['nav__max']
    fund.volatility = (fund.max_nav - fund.min_nav) / fund.min_nav * 100
    fund.last_52_week_price_set = fund.get_last_52_week_price_set_until(fund.current_price.date)
    fund.price_overview = fund.price_set.filter(date__gte=fund.current_price.date - timedelta(365.25 * 8))[::10]

    return render_to_response('fundtracking/view.html', {'fund': fund}, context_instance = RequestContext(request))
