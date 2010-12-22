'''
File: urls.py
Author: Leong Seh Hui
Description: Routing information for fund pages
'''
from django.conf.urls.defaults import *
from piston.resource import Resource
from api.handlers import FundHandler, PriceHandler

fund_handler = Resource(FundHandler)
price_handler = Resource(PriceHandler)

urlpatterns = patterns('',
    (r'funds\.(?P<emitter_format>.+)', fund_handler),
    (r'funds/(?P<fund_id>\d+)\.(?P<emitter_format>.+)', fund_handler),
    (r'funds/(?P<fund_code>[a-zA-Z ]+)\.(?P<emitter_format>.+)', fund_handler),

    (r'prices\.(?P<emitter_format>.+)', price_handler),
    (r'prices/history/(?P<fund_id>\d+)\.(?P<emitter_format>.+)', price_handler, {'action': 'history'}),
    (r'prices/history/(?P<fund_code>[a-zA-Z ]+)\.(?P<emitter_format>.+)', price_handler, {'action': 'history'}),
)
