'''
File: urls.py
Author: Leong Seh Hui
Description: Routing information for fund pages
'''
from django.conf.urls.defaults import patterns 
from piston.doc import documentation_view
from piston.resource import Resource
from mutualtracker.api.handlers.fundtracking import FundHandler, PriceHandler
#from mutualtracker.api.handlers.reporttracking import ReportHandler

fund_handler = Resource(FundHandler)
price_handler = Resource(PriceHandler)
#report_handler = Resource(ReportHandler)

urlpatterns = patterns('',
    (r'funds\.(?P<emitter_format>.+)', fund_handler),
    (r'funds/((?P<fund_id>\d+)|(?P<fund_code>[a-zA-Z ]+))\.(?P<emitter_format>.+)', fund_handler),
    (r'funds/((?P<fund_id>\d+)|(?P<fund_code>[a-zA-Z ]+))/prices\.(?P<emitter_format>.+)', fund_handler, {'action': 'list_prices'}),

    (r'prices\.(?P<emitter_format>.+)', price_handler),
    
    # Automated documentation
    (r'^$', documentation_view),

    # Obsolete
    (r'prices/history/((?P<fund_id>\d+)|(?P<fund_code>[a-zA-Z ]+))\.(?P<emitter_format>.+)', fund_handler, {'action': 'list_prices'}),
)
