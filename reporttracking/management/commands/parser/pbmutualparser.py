from decimal import Decimal
import re
import utils
import logging
import unicodedata
from base import AccumulateType, LineType, RegionType, LineData

class ParseState:
    (Init, WaitingHeader, AccumulatingLines, AccumulatingNotes, Parsing, Stop) = range(0, 6)

# Parsing class
class PbMutualAnnualReportParser():
    # Constants
    BEGIN_PARSE_TOKEN = 'EQUITY SECURITIES - '
    END_PARSE_TOKEN = (
        'TOTAL QUOTED INVESTMENTS',
        'TOTAL QUOTED EQUITY SECURITIES',
    )
    CHANGE_PAGE_TOKEN = (
        'For the Financial Year Ended', # Header
        'Notes To The Financial Statements', # Header
        'Per Cent', # Table header
#        '\xb7', # Footer
    )
    TABLE_HEADER_TOKEN = '000 %'
    COUNTRY_SECTIONS = {
        'IN MALAYSIA': RegionType.Malaysia,
        'QUOTED - IN MALAYSIA': RegionType.Malaysia,
        'OUTSIDE MALAYSIA': RegionType.Foreign,
        'QUOTED - OUTSIDE MALAYSIA': RegionType.Foreign,
    }
    INDUSTRIES = set([
        'Airlines',
        'Airlines / Transportation',
        'Apparel / Real Estate',
        'Basic Materials',
        'Building Materials',
        'Chemicals / Electronics',
        'Chemicals / Real Estate',
        'Commercial Services / Real Estate',
        'Commercial Services / Transportion',
        'Commercial Services',
        'Communications',
        'Consumer, Cyclical',
        'Consumer, Non-Cyclical', #TODO: Same as above, will figure out some way to merge them together
        'Consumer, Non-cyclical',
        'Distribution / Wholesale / Water',
        'Diversified Financial Services / Real Estate',
        'Diversified',
        'Electric',
        'Electrical Components & Equipment',
        'Electronics',
        'Energy - Alternative Sources',
        'Energy',
        'Engineering & Construction / Transportation',
        'Engineering & Construction / Real Estate',
        'Engineering & Construction',
        'Environment Control / Water',
        'Financial',
        'Funds',
        'Gas',
        'Holding Companies - Diversified',
        'Home Builders',
        'Industrial',
        'Investment Companies',
        'Lodging',
        'Leisure Time',
        'Machinery - Construction & Mining',
        'Miscellaneous Manufacturer',
        'Pipelines / Gas',
        'REITS',
        'Real Estate',
        'Retail',
        'Technology',
        'Telecommunications',
        'Transportation',
        'Trucking & Leasing / Transportation',
        'Trusts',
        'Utilities',
    ])
    TOKENS_TO_IGNORE = set([
        'MYR000',
        'MYR\'000',
        '(cont\'d)',
    ])
    DATA_LINE_RE = re.compile(r'([0-9]{1,3}(,[0-9]{3})*(\.[0-9]+)?)')
    COUNTRY_LINE_RE = re.compile(r'In( the)? (?P<country>[\w ]+)( \(contd\))?', re.IGNORECASE)
    DATE_RE = re.compile(r'\d{1,2} (January|February|March|April|May|June|July|August|September|October|November|December) \d{4}')
    NOTE_SECTION_RE = re.compile(r'^Note \((?P<note_num>\w+)\)\s?:')
    COMPANY_NOTE_RE = re.compile(r'\[Note\s?\((?P<note_num>\w+)\)\]')
    DATA_DASHES_RE = re.compile(r'(\s-\s|\s-$)')
    FOOTER_RE = re.compile(r'^\d+ (.*?(PB|Public).*? Fund.*?){2} \d+$', re.IGNORECASE)
    REPORT_SUBSECTION_RE = re.compile(r'^\(\w\) ')

    def parse(self, report):
        self.state = ParseState.Init
        self.security_type = ''
        self.current_industry = ''
        self.current_country = 'Malaysia'
        self.acc_line = ''
        self.acc_type = AccumulateType._Invalid
        self.last_parsed_data = LineData()
        self.last_match = None
        self.current_note = ''
        self.note_references = {}

        logging.debug('### Start parsing')
        reportData = []
        for line in report:
            line_text = unicodedata.normalize('NFKD', unicode(line.strip(), 'utf-8'))

            if self.state != ParseState.Init:
                logging.debug('** {0}##{1}'.format(repr(line.strip()), self.state))

            # Major halting points
            if self._matchEndParse(line_text) or (self.last_parsed_data.name in self.END_PARSE_TOKEN):
                break

            # Parser FSM
            if self.state == ParseState.Init:
                if line_text.find(self.BEGIN_PARSE_TOKEN) != -1:
                    self.state = ParseState.WaitingHeader

            elif self.state == ParseState.WaitingHeader:
                if line_text.find(self.TABLE_HEADER_TOKEN) != -1:
                    self.state = ParseState.Parsing

            elif self.state == ParseState.Parsing:
                # Sections that should trigger a change page
                if self._matchHeaderFooter(line_text):
                    self.state = ParseState.WaitingHeader

                # If it's the notes section, let it accumulate lines
                elif self._matchNoteSection(line_text):
                    self.acc_line = line_text
                    self.state = ParseState.AccumulatingNotes

                # Country lines
                elif line_text in self.COUNTRY_SECTIONS:
                    if self.COUNTRY_SECTIONS[line_text] == RegionType.Malaysia:
                        self.current_country = 'Malaysia'
                        # Ignore the Outside Malaysia header
                elif self._matchCountryLine(line_text):
                    self._extractCountry()

                # Industry line
                elif self._matchIndustry(line_text):
                    self._extractIndustry(line_text)

                # Lines to actively ignore
                elif self.DATE_RE.search(line_text):
                    pass
                elif line_text in self.TOKENS_TO_IGNORE:
                    pass

                # Data line
                elif self._matchDataLine(line_text):
                    reportData.append(self._extractDataLine(line_text, self.last_match))

                # Accumulate lines otherwise
                else:
                    self.state = ParseState.AccumulatingLines
                    self.acc_line = line_text

                    if self.acc_line.isupper():
                        self.acc_type = AccumulateType.SecuritiesType
                    else:
                        self.acc_type = AccumulateType.CompanyName

            elif self.state == ParseState.AccumulatingLines:
                combined_line = '{0} {1}'.format(self.acc_line, line_text)
                if self._matchDataLine(line_text, len(self.acc_line) + 1):
                    reportData.append(self._extractDataLine(combined_line, self.last_match))
                    self.state = ParseState.Parsing

                elif self._matchIndustry(line_text) and self.current_industry != line_text \
                        and not (self.acc_line == 'Singapore' and line_text == 'Telecommunications') \
                        and not (self.acc_line == 'Far Eastone' and line_text == 'Telecommunications'):
                    self._extractIndustry(line_text)
                    self.security_type = self.acc_line
                    self.acc_type = AccumulateType._Invalid
                    self.state = ParseState.Parsing

                elif self._matchIndustry(combined_line):
                    self._extractIndustry(combined_line)
                    self.security_type = self.acc_line
                    self.acc_type = AccumulateType._Invalid
                    self.state = ParseState.Parsing

                elif (line_text.isupper() and self.acc_type == AccumulateType.SecuritiesType) \
                        or (self.acc_type == AccumulateType.CompanyName):
                    self.acc_line = combined_line

                elif self._matchCountryLine(line_text):
                    self._extractCountry()
                    self.security_type = self.acc_line
                    self.acc_type = AccumulateType._Invalid
                    self.state = ParseState.Parsing

                else:
                    self.acc_line = line_text
                    self.acc_type = AccumulateType.CompanyName

            elif self.state == ParseState.AccumulatingNotes:
                has_complete_note = True
                #TODO: Code smell, I shouldn't be needing to do this
                note_num = self.current_note
                note = self.acc_line
                # Sections that should trigger a change page
                if self._matchHeaderFooter(line_text):
                    self.state = ParseState.WaitingHeader

                # If it's the notes section, let it accumulate lines
                elif self._matchNoteSection(line_text):
                    self.acc_line = line_text

                # Country lines
                elif line_text in self.COUNTRY_SECTIONS:
                    if self.COUNTRY_SECTIONS[line_text] == RegionType.Malaysia:
                        self.current_country = 'Malaysia'
                        # Ignore the Outside Malaysia header
                    self.state = ParseState.Parsing
                elif self._matchCountryLine(line_text):
                    self._extractCountry()
                    self.state = ParseState.Parsing

                # Industry line
                elif utils.rchop(line_text, ' (cont\'d)') in self.INDUSTRIES:
                    self.current_industry = utils.rchop(line_text, ' (cont\'d)')
                    self.state = ParseState.Parsing

                else:
                    has_complete_note = False
                    self.acc_line += ' ' + line_text

                if has_complete_note:
                    self.note_references[note_num].note = note

        return reportData

    def _matchHeaderFooter(self, line_text):
        if self.FOOTER_RE.match(line_text):
            return True

        for token in self.CHANGE_PAGE_TOKEN:
            if line_text.find(token) != -1:
                return True
        return False

    def _matchNoteSection(self, line_text):
        match = self.NOTE_SECTION_RE.match(line_text)
        if match:
            self.current_note = match.group('note_num')
            return True
        return False

    def _matchCountryLine(self, line_text):
        self.last_match = self.COUNTRY_LINE_RE.match(line_text)

        return (self.last_match is not None)

    def _matchIndustry(self, line_text):
        #TODO: Is there a way to make it line_text.rchop(' (contd)') instead?
        return (utils.rchop(line_text, ' (cont\'d)') in self.INDUSTRIES)

    def _matchDataLine(self, line_text, offset=0):
        if self.DATE_RE.search(line_text):
            return False

        matches = [
            {
                'start': x.start() + offset,
                'end': x.end() + offset,
                'text': x.group(0).replace(',', '')
            }
            for x in self.DATA_LINE_RE.finditer(line_text)
        ]

        # Search for dashes which may mean a number too small
        matches.extend([
            {
                'start': dash.start() + offset + 1,
                'end': dash.end() + offset,
                'text': 0
            }
            for dash in self.DATA_DASHES_RE.finditer(line_text)
        ])
        def matchSort(a, b):
            return cmp(a['start'], b['start'])
        matches.sort(matchSort)

        # Some dashes may have been legitimate at the end of the company name, so just take the last four numbers
        if len(matches) > 4:
            matches = matches[-4:]

        self.last_match = matches
        data_len = len(self.last_match)
        return (data_len == 3 or data_len == 4)

    def _matchEndParse(self, line_text):
        if self.state == ParseState.Init:
            return False

        if self.REPORT_SUBSECTION_RE.search(line_text):
            return True

        return False

    def _extractCountry(self):
        self.current_country = self.last_match.group('country').strip()
        if self.current_country == 'MALAYSIA':
            self.current_country = 'Malaysia'

    def _extractIndustry(self, line_text):
        self.current_industry = utils.rchop(line_text, ' (cont\'d)')

    def _extractDataLine(self, line_text, matches):
        line_data = LineData()

        # Match the company names
        name_end = matches[0]['start'] - 1
        if name_end != -1:
            line_data.name = line_text[:name_end].strip()

        # Extract the note numbers if any
        match = self.COMPANY_NOTE_RE.search(line_data.name)
        if match:
            line_data.name = line_data.name[:match.start() - 1]
            self.note_references[match.group('note_num')] = line_data

        line_data.security_type = self.security_type
        if len(matches) == 4:
            line_data.type = LineType.Company
            line_data.industry = self.current_industry
            line_data.country = self.current_country
            line_data.quantity = Decimal(matches[0]['text'])
            line_data.cost = Decimal(matches[1]['text'])
            line_data.market_value = Decimal(matches[2]['text'])
            line_data.nav_percentage = Decimal(matches[3]['text'])
        elif len(matches) == 3:
            if line_data.name:
                line_data.industry = ''
                line_data.country = ''
                if line_data.name in self.END_PARSE_TOKEN:
                    line_data.type = LineType.GrandTotal
                #TODO: A very crude way to handle region totals, need refactoring
                elif line_data.name.find('in Malaysia') != -1 or line_data.name.find('Outside Malaysia') != -1:
                    line_data.type = LineType.RegionTotal
                else:
                    line_data.type = LineType.SecurityTotal
            else:
                line_data.industry = self.current_industry
                line_data.country = self.current_country
                line_data.type = LineType.IndustryTotal

            line_data.cost = Decimal(matches[0]['text'])
            line_data.market_value = Decimal(matches[1]['text'])
            line_data.nav_percentage = Decimal(matches[2]['text'])

        self.last_parsed_data = line_data
        return line_data

if __name__ == '__main__':
    import os.path
    import subprocess
    import sys
    import datachecker
    import logging

    logging.basicConfig(level=logging.DEBUG)
    for filename in sys.argv[1:]:
        if not os.path.isfile(filename):
            print 'ERROR: Cannot find report', filename
            sys.exit(1)

        text_filename = os.path.splitext(filename)[0] + '.txt'
        if not os.path.isfile(text_filename):
            subprocess.check_call(['pdftotext', '-raw', filename, text_filename])

        if not os.path.isfile(text_filename):
            print 'ERROR: Cannot find the text output'
            sys.exit(1)

        parser = PbMutualAnnualReportParser()
        with open(text_filename, 'r') as textfile:
            data = parser.parse(textfile)
            for line in data:
                print '{0}/{1}: {2}'.format(line.country, line.industry, line.name)
            datachecker.check(data)
