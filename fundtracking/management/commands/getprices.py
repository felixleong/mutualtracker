import urllib2
from datetime import datetime
from decimal import Decimal
from BeautifulSoup import BeautifulSoup
from django.core.management.base import NoArgsCommand, CommandError
from mutualtracker.fundtracking.models import Fund, Price

class Command(NoArgsCommand):
    PB_PRICES_URL = 'http://www.publicmutual.com.my/application/fund/fundprice.aspx'
    EXPECTED_HEADER = [
        'Date',
        'Fund',
        'Fund Abbreviation',
        'NAV',
        'Chg',
        'Chg %'
    ]

    def handle_noargs(self, **options):
        page = urllib2.urlopen(self.PB_PRICES_URL)
        if page.getcode() != 200:
            raise CommandError('Fail to fetch the page - status {0}'.format(page.getcode()))

        # Correctly identify the rows
        soup = BeautifulSoup(page)
        fund_table = soup.find('table', 'fundtable')
        if fund_table.tbody != None:
            fund_table = fund_table.tbody

        fund_rows = fund_table.findAll('tr')
        if len(fund_rows) < 2:
            raise CommandError('No price rows on latest price page')

        # Validate the header row
        header = [ col.find(text=True) for col in fund_rows[0].findAll('td') ]
        if header != self.EXPECTED_HEADER:
            raise CommandError('Table header mismatch')

        # Iterate through the table and save the prices
        for row in fund_rows[1:]:
            data = row.findAll('td')
            update_date = datetime.strptime(data[0].find(text=True).string, '%d/%m/%Y')
            name = data[1].find(text=True).string.title().replace('Pb', 'PB')
            code = data[2].find(text=True).string.__str__()
            nav = Decimal(data[3].find(text=True).string)
        
            try:
                fund = Fund.objects.get(code=code)
            except Fund.DoesNotExist:
                self.stdout.write('## Create new fund: {0}'.format(code))
                fund = Fund(code=code, name=name)
                fund.save()

            try:
                price_entry = Price.objects.get(fund=fund, date=update_date)

                if price_entry.nav != nav:
                    raise CommandError('NAV mismatch for fund %s', fund.code)
            except Price.DoesNotExist:
                self.stdout.write('## Adding price: {0} - {1}'.format(code, nav))
                price_entry = Price(fund=fund, date=update_date, nav=nav)
                price_entry.save()
