from piston.handler import BaseHandler
from mutualtracker.reporttracking.models import Report

class ReportHandler(BaseHandler):
    model = Report
    allowed_methods = ('GET',)

    def read(self, request, action=None, fund_id=None, fund_code=None):
        if action == 'history':
            return self.history(request, fund_id, fund_code)
        else:
            return self.list()

    def list(self, request, report_id=None):
        base = Report.objects
        if report_id:
            return base.get(pk=report_id)
        else:
            return base.all()
