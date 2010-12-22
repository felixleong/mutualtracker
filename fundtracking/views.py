'''
File: views.py
Author: Seh Hui "Felix" Leong
Description: Views for fund tracking page
'''
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from fundtracking.models import Fund, Price

def index(request):
    """Retrieve a fund listing"""
    fund_list = Fund.objects.all().order_by('code')
    return render_to_response('fundtracking/index.html', {'fund_list': fund_list}, context_instance = RequestContext(request))

def view(request, fund_id=None, code=None):
    """Get a detailed view of the requested fund"""
    if fund_id:
        fund = get_object_or_404(Fund, pk=fund_id)
    else:
        fund = get_object_or_404(Fund, code=code)

    current_price = fund.price_set.all()[0]
    previous_price = fund.price_set.all()[1]
    price_difference = current_price.nav - previous_price.nav
    price_difference_percentage = price_difference / previous_price.nav * 100

    last_52_week_max_price = fund.last_52_week_ceiling_price
    last_52_week_min_price = fund.last_52_week_floor_price
    volatility = (last_52_week_max_price - last_52_week_min_price) / last_52_week_min_price * 100

    data = {
        'fund': fund,
        'price_overview': fund.price_set.all()[::10],
        'current_price': current_price,
        'previous_price': previous_price,
        'price_difference': price_difference,
        'price_difference_percentage': price_difference_percentage,
        'last_52_week_max_price': last_52_week_max_price,
        'last_52_week_min_price': last_52_week_min_price,
        'volatility': volatility,
        'price_history_5_days': fund.price_set.all()[0:5],
    }
    return render_to_response('fundtracking/view.html', data, context_instance = RequestContext(request))
