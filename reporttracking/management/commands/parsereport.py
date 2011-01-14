import logging
import os.path
import subprocess
import unicodedata
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from mutualtracker.reporttracking.models import Report, Country, Industry, Company, Holding
from parser import PbMutualAnnualReportParser, datachecker
from parser.base import LineData, LineType

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--commit',
            action='store_true',
            dest='commit',
            default=False,
            help='Commits the report details into the database'
        ),
    )
    parser = PbMutualAnnualReportParser()

    def handle(self, *args, **options):
#        logging.basicConfig(level=logging.DEBUG)
        commit=options['commit']

        # Filter only annual reports that are downloaded but not yet parsed
        for report in Report.objects.filter(type=1, state=1):
            self.stdout.write('## Parsing ID#{0}: {1} - {2}: {3}\n'.format(report.pk, report.fund, report.date, report.file_name.path))
            text_filename = self._convertPdfToTextFile(report.file_name.path)

            with open(text_filename, 'r') as textfile:
                data = self.parser.parse(textfile)
                try:
                    datachecker.check(data)
                    self._commitData(data, report, commit)
                except Exception, exc:
                    raise CommandError('Data checking failed, last line:\n{0}'.format(exc))

                self.stdout.write('\n')

    def _convertPdfToTextFile(self, filename):
        '''Converts PDF file to a text file and returns the filename of the text file.'''
        try:
            if not os.path.isfile(filename):
                raise CommandError('Cannot find report - {0}'.format(filename))

            text_filename = os.path.splitext(filename)[0] + '.txt'

            # If the PDF have already been converted, return the text file
            if os.path.isfile(text_filename):
                return text_filename

            # Perform the conversion
            subprocess.check_call(['pdftotext', '-raw', filename, text_filename])
            if not os.path.isfile(text_filename):
                raise CommandError('Cannot find the text output')

            return text_filename
        except subprocess.CalledProcessError, exc:
            raise CommandError('pdftotext failed, returned {0}'.format(exc.returncode))

    def _commitData(self, data, report, commit=False):
        '''Commit the parsed data into the database'''
        prev_line = LineData()

        for line in data:
            if line.type != LineType.Company:
                continue

            if prev_line.security_type != line.security_type:
                pass # Does nothing at the moment; we still don't track such info yet
            if prev_line.country != line.country:
                current_country = self._getCountry(line.country, commit)
            if prev_line.industry != line.industry:
                current_industries = [ self._getIndustry(x.strip(), commit) for x in line.industry.split('/') ]

            # Get the company
            try:
                company = Company.objects.get(name=line.name, country=current_country)
            except Company.DoesNotExist:
                self.stdout.write(' +-- (!!) Create company: [{1}] {0}\n'.format(line.name, current_country.name))
                self.stdout.write('      * with industries: {0}\n'.format(','.join([ x.name for x in current_industries ])))
                company = Company(name=line.name, country=current_country)
                if commit:
                    company.save()

            if commit:
                # Attach any potential new industries to the company, just in case
                for industry in current_industries:
                    company.industries.add(industry)
                company.save()
            else:
                if company.pk:
                    # Mention any differences in the industries tuple
                    company_industries = company.industries.all()
                    for industry in current_industries:
                        if industry not in company_industries:
                            self.stdout.write('      * new industry association: {0}\n'.format(industry.name))

            # Once we had the company, add it to the holdings of the report
            self._addHoldingToReport(report, company, line, commit)

            # Done, prepare to get the next line
            prev_line = line

        # Update the parsing status
        report.state = 2 # Parsed
        if commit:
            report.save()

    def _addHoldingToReport(self, report, company, line, commit):
        '''Associate fund holding data in report and adding it into the database.'''
        if not commit:
            self.stdout.write(' +-- Add holding: [{1}] {0} = {2} {3} {4} {5}\n'.format(
                company.name, company.country.name,
                line.quantity,
                line.cost,
                line.market_value,
                line.nav_percentage))
            return

        try:
            holding = Holding.objects.get(report=report, company=company)

            # Update if data is inaccurate
            if holding.quantity != line.quantity or \
                    holding.cost != line.cost or \
                    holding.value != line.market_value or \
                    holding.percentage_of_nav != line.nav_percentage:
                holding.quantity = line.quantity
                holding.cost = line.cost
                holding.value = line.market_value
                holding.percentage_of_nav = line.nav_percentage
                holding.save()
        except Holding.DoesNotExist:
            holding = Holding(
                report=report, company=company,
                quantity=line.quantity,
                cost=line.cost,
                value=line.market_value,
                percentage_of_nav=line.nav_percentage)
            holding.save()

    def _getCountry(self, name, commit):
        '''Gets the company model object; creates a new object if it does not exists.'''
        try:
            current_country = Country.objects.get(name=name)
        except Country.DoesNotExist:
            self.stdout.write(' +-- Create country: {0}'.format(name))
            current_country = Country(name=name)
            if commit:
                current_country.save()
        finally:
            return current_country

    def _getIndustry(self, name, commit):
        '''Gets the industry model object; creates a new object if it does not exists.'''
        try:
            industry = Industry.objects.get(name=name)
        except Industry.DoesNotExist:
            self.stdout.write(' +-- Create Industry: {0}'.format(name))
            industry = Industry(name=name)
            if commit:
                industry.save()
        finally:
            return industry

