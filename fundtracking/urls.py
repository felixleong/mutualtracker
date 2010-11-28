'''
File: urls.py
Author: Leong Seh Hui
Description: Routing information for fund pages
'''
from django.conf.urls.defaults import *

urlpatterns = patterns('fundtracking.views',
    (r'^$', 'index'),
)
