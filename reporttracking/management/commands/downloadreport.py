import urllib2
from django.core.management.base import NoArgsCommand, CommandError
from downloader import PBMutualReportDownloader
from mutualtracker.fundtracking.models import Fund
from mutualtracker.reporttracking.models import Report

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        downloader = None
        try:
            downloader = PBMutualReportDownloader()

            if downloader.login():
                self.stdout.write('Logged in\n')

                for fund in Fund.objects.all():
                    # The report code in PBMutual Online has no spaces, hence we need to remove them
                    self.stdout.write('Handling {0}...'.format(fund.code))
                    fund_code = str(fund.code).translate(None, ' ')
                    listing = downloader.getReportListing(fund_code)
                    self.stdout.write(' report count: {0}\n'.format(len(listing)))

                    # Go through the listings and check whether there's any new report
                    for index, report_meta in enumerate(listing):
                        if report_meta.type == -1:
                            raise CommandError("Unexpected report type")

                        self.stderr.write('-- index: {0}: '.format(index))
                        # If the report does not exist in the database, download a copy
                        if not Report.objects.filter(fund__code=fund.code, date=report_meta.date, type=report_meta.type):
                            self.stdout.write('!! Downloading report: date={0}\n'.format(report_meta.date))
                            report_file = downloader.getReport(fund.code, index)
                            self.stdout.write('!! Download completed!\n')
                            if not report_file:
                                raise CommandError("Couldn't download the file for fund %s, %s", fund.code, report.date.strftime('%Y-%m-%d'))

                             # Save the report
                            report = Report()
                            report.fund = fund
                            report.date = report_meta.date
                            report.type = report_meta.type
                            report.state = 1 # Downloaded
                            report.file_name.save(report_file['filename'], report_file['file_content'])
                            report.save()
                        else:
                            self.stdout.write('## Skipped report: date={0}\n'.format(report_meta.date))
            else:
                self.stderr.write('Forced out from system, please try again\n')
        except urllib2.HTTPError, exc:
            raise CommandError("The server couldn't fulfill the request, code=%d", exc.code)
        except urllib2.URLError, exc:
            raise CommandError("Failed to reach server, reason=%s", exc.reason)
        finally:
            if downloader:
                downloader.logout()
                self.stdout.write('Logged out\n')

