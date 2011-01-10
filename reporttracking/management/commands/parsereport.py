import logging
import os.path
import subprocess
import unicodedata
from django.core.management.base import NoArgsCommand, CommandError
from mutualtracker.reporttracking.models import Report, Country, Industry, Company, Holding
from parser import PbMutualAnnualReportParser, datachecker
from parser.base import LineData, LineType

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
#        logging.basicConfig(level=logging.DEBUG)
        parser = PbMutualAnnualReportParser()

        # Filter only annual reports that are downloaded but not yet parsed
        for report in Report.objects.filter(type=1, state=1):
            self.stdout.write('## Parsing {0} - {1}: {2}\n'.format(report.fund, report.date, report.file_name.path))
            text_filename = self._convertPdfToTextFile(report.file_name.path)

            with open(text_filename, 'r') as textfile:
                data = parser.parse(textfile)
#                for line in data:
#                    self.stderr.write(line.name + '\n')
                try:
                    datachecker.check(data)
                    self._commitData(data, report)
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

    def _commitData(self, data, report, dry_run=True):
        '''Commit the parsed data into the database'''
        prev_line = LineData()

        for line in data:
            if line.type != LineType.Company:
                continue

            if prev_line.security_type != line.security_type:
                pass # Does nothing at the moment; we still don't track such info yet
            if prev_line.country != line.country:
                current_country = self._getCountry(line.country)
            if prev_line.industry != line.industry:
                current_industries = [ self._getIndustry(x.strip(), dry_run) for x in line.industry.split('/') ]

            # Get the company
            try:
                company = Company.objects.get(name=line.name, country=current_country)
            except Company.DoesNotExist:
                self.stdout.write(' +-- (!!) Create company: [{1}] {0}\n'.format(line.name, current_country.name))
                self.stdout.write('      * with industries: {0}\n'.format(','.join([ x.name for x in current_industries ])))
                company = Company(name=line.name, country=current_country)

            if not dry_run:
                # Attach any potential new industries to the company, just in case
                for industry in current_industries:
                    company.industries.add(industry)
                company.save()
            else:
                if company.pk:
                    # Mention any differences in the industries tuple
                    for industry in company.industries.all():
                        if industry not in current_industries:
                            self.stdout.write('      * new industry association: {0}\n'.format(industry.name))

            # Once we had the company, add it to the holdings of the report
            self._addHoldingToReport(report, company, line, dry_run)

            # Done, prepare to get the next line
            prev_line = line

        # Update the parsing status
        report.state = 2 # Parsed
        if not dry_run:
            report.save()

    def _addHoldingToReport(self, report, company, line, dry_run=True):
        '''Associate fund holding data in report and adding it into the database.'''
        if dry_run:
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

    def _getCountry(self, name, dry_run=True):
        '''Gets the company model object; creates a new object if it does not exists.'''
        try:
            current_country = Country.objects.get(name=name)
        except Country.DoesNotExist:
            self.stdout.write(' +-- Create country: {0}'.format(name))
            current_country = Country(name=name)
            if not dry_run:
                current_country.save()
        finally:
            return current_country

    def _getIndustry(self, name, dry_run=True):
        '''Gets the industry model object; creates a new object if it does not exists.'''
        try:
            industry = Industry.objects.get(name=name)
        except Industry.DoesNotExist:
            self.stdout.write(' +-- Create Industry: {0}'.format(name))
            industry = Industry(name=name)
            if not dry_run:
                industry.save()
        finally:
            return industry

