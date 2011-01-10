# Enumeration classes
class AccumulateType:
    (_Invalid, SecuritiesType, CompanyName) = range(0, 3)
class LineType:
    (_Invalid, SecurityType, Industry, Company, IndustryTotal, RegionTotal, SecurityTotal, GrandTotal) = range(0, 8)
class RegionType:
    (_Invalid, Malaysia, Foreign) = range(0, 3)

# Data class
class LineData():
    security_type = ''
    industry = ''
    country = ''
    type = LineType._Invalid
    name = ''
    note = None
    quantity = 0
    cost = 0
    market_value = 0
    nav_percentage = 0

    def __str__(self):
        return '{0} - {1}: {2}'.format(self.country, self.industry, self.name)
