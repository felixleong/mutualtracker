from base import AccumulateType, LineType, RegionType, LineData
import logging

def check(data):
    security_total = LineData()
    industry_total = LineData()
    grand_total = LineData()
    prev_line = LineData()

    logging.debug('### Start checking')
    for line in data:
        if line.type == LineType.Company:
            if prev_line.security_type != line.security_type:
                logging.debug('@@ Reseting due to security change {0}, {1}'.format(prev_line.security_type, line.security_type))
                security_total = LineData()
                industry_total = LineData()

            if prev_line.country != line.country or prev_line.industry != line.industry:
                logging.debug('@@ Reseting due to country or industry change {0}/{1}, {2}/{3}'.format(prev_line.country, prev_line.industry, line.country, line.industry))
                industry_total = LineData()

            _addToTotal(line, industry_total)
            _addToTotal(line, security_total)
            _addToTotal(line, grand_total)
        elif line.type == LineType.IndustryTotal:
            if not _compareTotals(industry_total, line):
                raise Exception('Mismatched totals - industry: {0}/{1}'.format(line.country, line.industry))
        elif line.type == LineType.SecurityTotal:
            if not _compareTotals(security_total, line):
                raise Exception('Mismatched totals - security type: {0}'.format(line.name))
        elif line.type == LineType.GrandTotal:
            if not _compareTotals(grand_total, line):
                raise Exception('Mismatched totals - grand total')
        elif line.type == LineType.RegionTotal:
            security_total = LineData()
            industry_total = LineData()
        else:
            raise Exception('Invalid line type - {0}: {1}'.format(line.name, line.type))

        prev_line = line

#    if data and prev_line.type != LineType.GrandTotal:
#        raise Exception('Last line is not grand total: {0}'.format(prev_line.type))


def _addToTotal(line, total):
    total.cost = total.cost + line.cost
    total.market_value = total.market_value + line.market_value
    total.nav_percentage = total.nav_percentage + line.nav_percentage

def _compareTotals(current, expected):
    def _printData(heading, line):
        logging.debug('{0}:: Cost: {1}\nMarket value: {2}\nNAV: {3}'.format(heading, line.cost, line.market_value, line.nav_percentage))

    _printData('CURRENT', current)
    _printData('EXPECTED', expected)

    return (
        current.cost == expected.cost and
        current.market_value == expected.market_value and
        current.nav_percentage == expected.nav_percentage
    )
