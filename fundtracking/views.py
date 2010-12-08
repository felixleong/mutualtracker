'''
File: views.py
Author: Seh Hui "Felix" Leong
Description: Views for fund tracking page
'''
from django.template import RequestContext
from django.shortcuts import render_to_response
from fundtracking.models import Fund, Price

def index(request):
    """Retrieve a fund listing"""
    fund_list = Fund.objects.all().order_by('code')
    return render_to_response('fundtracking/index.html', {'fund_list': fund_list}, context_instance = RequestContext(request))

def view(request, id):
    """Get a detailed view of the requested fund"""
    pass
