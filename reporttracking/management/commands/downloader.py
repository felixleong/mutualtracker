from datetime import datetime
import logging
import re
import urllib
import urllib2
from BeautifulSoup import BeautifulSoup, SoupStrainer
from django.core.files.base import ContentFile
from mutualtracker.reporttracking.models import Report


class ReportData():
    """Metadata of the report row"""
    date = None
    type = -1
    has_english = False
    has_chinese = False
    has_malay = False

    def __str__(self):
        return '%s: %s' % (self.strftime('%Y-%m-%d'), type)


class PBMutualReportDownloader():
    """Report downloader for Public Mutual"""
    # Constants
    PBMUTUAL_URL='https://www.publicmutualonline.com.my'
    USER_AGENT='Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10'
    PAGES={
        'Home': 'Default.aspx',
        'Login': 'PMBLogin.aspx',
        'Logout': 'Logout.aspx',
        'SecurityLogout': 'SecurityLogout.aspx',
        'ReportDownload': 'EReportDownload.aspx',
    }
    PBMUTUAL_USERNAME='FELIXLEONG'
    PBMUTUAL_PASSWORD='R84rtiNMS'
    PDF_CONTENT_DISP_RE = re.compile(r'filename=(?P<filename>.+\.(pdf|PDF))')
    LISTING_STRAINER = SoupStrainer('table', id='gvwEReport')

    HTTP_DEBUG_LEVEL=False

    # Class methods
    def __init__(self):
        """Construct the downloader instance"""
        self._logger = logging.getLogger('ReportDownloader')

        # Setup our URL opener
        opener = urllib2.build_opener(
                urllib2.HTTPHandler(debuglevel=self.HTTP_DEBUG_LEVEL),
                urllib2.HTTPSHandler(debuglevel=self.HTTP_DEBUG_LEVEL),
                urllib2.HTTPCookieProcessor())
        urllib2.install_opener(opener)

        # Retrieve our ViewState before doing anything
        response = urllib2.urlopen(self._getUrl('Login'))
        self._last_view_state = self._getViewState(response.read())

    def login(self, username=PBMUTUAL_USERNAME, password=PBMUTUAL_PASSWORD):
        """Perform a login in the PB Mutual Online system and returns True if
        successful."""
        self._logger.info('Logging into Public Mutual Online')
        params = {
            '__VIEWSTATE': self._last_view_state,
            '__EVENTTARGET': 'LoginButton',
            'txtUserName': username,
            'txtPassword': password,
        }
        response = self._openUrl(self._getUrl('Login'), params)

        if response.geturl() != self._getUrl('Home'):
            self._logger.error('Failed to login, received page: %s', response.geturl())
            return False
        else:
            return True

    def getReportListing(self, fund_code):
        """Retrieves fund listing based on fund code provided and returns a list."""
        self._logger.info('Retrieving report listing of %s' % (fund_code,))

        response = self._openUrl(self._getUrl('ReportDownload'))
        response_html = response.read()
        view_state = self._getViewState(response_html)
        self._logger.debug('### Report cover page:\n%s', response_html)

        params = {
            '__VIEWSTATE': view_state,
            '__VIEWSTATEENCRYPTED': '',
            '__EVENTTARGET': 'ddlERTFundName',
            '__EVENTARGUMENT': '',
            'ddlERTFundName': fund_code,
        }
        response = self._openUrl(self._getUrl('ReportDownload'), params)
        response_html = response.read()

        if response.geturl() != self._getUrl('ReportDownload'):
            self._logger.error('Failed to retrieve listing, received page: %s', response.geturl())
            return []
        else:
            self._logger.debug('### Report listing:\n%s', response_html)

            self._last_view_state = self._getViewState(response_html)
            return self._parseReportListing(response_html)

    def getReport(self, fund_code, row_index):
        """Download the fund's report, referenced by the row index of the
        report entry and returns the filename.
        
        Keyword arguments:
        fund_code -- Fund code
        row_index -- The report row index
        """
        self._logger.info('Downloading report for fund %s: index %d', fund_code, row_index)
        params = {
            '__VIEWSTATE': self._last_view_state,
            '__VIEWSTATEENCRYPTED': '',
            '__EVENTTARGET': 'gvwEReport',
            '__EVENTARGUMENT': 'E_Id$%d' % (row_index, ),
            'ddlERTFundName': fund_code,
        }
        response = self._openUrl(self._getUrl('ReportDownload'), params)
        self._logger.debug('### Response headers: %s', response.info())
        content_disposition = response.info()['Content-Disposition']
        filename_match = self.PDF_CONTENT_DISP_RE.search(content_disposition)

        if filename_match:
            filename = filename_match.group('filename')
            self._logger.info('Downloading report: %s', filename)
            file_content = response.read()

            return {
                'filename': filename,
                'file_content': ContentFile(file_content),
            }
        else:
            self._logger.error('Cannot detect filename, content-disposition=%s', content_disposition)
            return {}

    def logout(self):
        """Logs out from the PB Mutual Tracker site."""
        self._logger.info('Logging out from Public Mutual Online')
        self._openUrl(self._getUrl('Logout'))

    def _getUrl(self, page):
        """Returns the full URL based on the page alias specified in PAGES."""
        return '%s/%s' % (self.PBMUTUAL_URL, self.PAGES[page])

    def _getViewState(self, content):
        """Returns the ASP.NET VIEWSTATE value from the page content."""
        soup = BeautifulSoup(content)
        return soup.find(id='__VIEWSTATE')['value']

    def _parseReportListing(self, report_listing_html):
        """Parse the report listing page and returns a list of downloadable reports."""
        table = BeautifulSoup(report_listing_html, parseOnlyThese=self.LISTING_STRAINER)

        listing = []
        for row in table.findAll('tr')[1:]:
            report_meta = [ ''.join(td.findAll(text=True)).strip() for td in row.findAll('td') ]

            # Parse the data text
            report_data = ReportData()
            report_data.date = datetime.strptime(report_meta[0], '%d/%m/%Y')
            report_data.has_english = (report_meta[2] == 'Download')
            for index, type in Report.REPORT_TYPE_CHOICES:
                if type == report_meta[1]:
                    report_data.type = index
            report_data.has_chinese = (report_meta[3] == 'Download')
            report_data.has_malay = (report_meta[4] == 'Download')

            listing.append(report_data)

        return listing

    def _openUrl(self, url, post_param=None, referer=''):
        """Opens URL and returns the page content.
        
        Keyword arguments:
        url -- The URL to be accessed.
        post_param -- The POST parameters to be submitted to the page.
        referer -- Specify the referring page that leads to this page request.
        """
        if post_param:
            params_data = urllib.urlencode(post_param)
        else:
            params_data = None
        request = urllib2.Request(url, params_data)
        request.add_header('User-Agent', self.USER_AGENT)
        if referer:
            request.add_header('Referer', referer)
        else:
            request.add_header('Referer', url)

        return urllib2.urlopen(request)

