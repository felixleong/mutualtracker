'''
File: views.py
Author: Seh Hui "Felix" Leong
Description: Views for fund tracking page
'''
from django.shortcuts import render_to_response
from fundtracking.models import Fund, Price

def index(request):
    """The index page"""
    pass

def _getMinMax():
    """docstring for _getMinMax"""
    pass
def _getLatest52WeekMinMaxPrice(fund_id):
    """Retrieves the floor and ceiling fund price within a 52-week period"""
    pass
