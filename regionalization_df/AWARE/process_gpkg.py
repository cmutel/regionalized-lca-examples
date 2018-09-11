# Convert KMZ downloaded from AWARE site using the following:
# ogr2ogr -f GPKG aware_prelim.gpkg AWARE_v1_2April_7th.kmz


example_string = """<html xmlns:fo="http://www.w3.org/1999/XSL/Format" xmlns:msxsl="urn:schemas-microsoft-com:xslt"><head><META http-equiv="Content-Type" content="text/html"><meta http-equiv="content-type" content="text/html; charset=UTF-8"></head><body style="margin:0px 0px 0px 0px;overflow:auto;background:#FFFFFF;"><table style="font-family:Arial,Verdana,Times;font-size:12px;text-align:left;width:100%;border-collapse:collapse;padding:3px 3px 3px 3px"><tr style="text-align:center;font-weight:bold;background:#9CBCE2"><td>0</td></tr><tr><td><table style="font-family:Arial,Verdana,Times;font-size:12px;text-align:left;width:100%;border-spacing:0px; padding:3px 3px 3px 3px"><tr><td>FID</td><td>0</td></tr><tr bgcolor="#D4E4F3"><td>Consumption_m3</td><td>0.0e+000</td></tr><tr><td>Area_m2</td><td>3.4e+008</td></tr><tr bgcolor="#D4E4F3"><td>Jan</td><td>-9999</td></tr><tr><td>Feb</td><td>-9999</td></tr><tr bgcolor="#D4E4F3"><td>Mar</td><td>-9999</td></tr><tr><td>Apr</td><td>-9999</td></tr><tr bgcolor="#D4E4F3"><td>May</td><td>-9999</td></tr><tr><td>Jun</td><td>-9999</td></tr><tr bgcolor="#D4E4F3"><td>Jul</td><td>-9999</td></tr><tr><td>Aug</td><td>-9999</td></tr><tr bgcolor="#D4E4F3"><td>Sep</td><td>-9999</td></tr><tr><td>Oct</td><td>-9999</td></tr><tr bgcolor="#D4E4F3"><td>Nov</td><td>-9999</td></tr><tr><td>Dec</td><td>-9999</td></tr><tr bgcolor="#D4E4F3"><td>Annual agri</td><td>-9999</td></tr><tr><td>Annual non-agri</td><td>-9999</td></tr><tr bgcolor="#D4E4F3"><td>Annual unknown</td><td>-9999</td></tr></table></td></tr></table></body></html>"""

from html.parser import HTMLParser
import fiona


class StupidHTMLParser(HTMLParser):
    def __init__(self):
        self.data = []
        super().__init__()

    def handle_starttag(self, tag, attrs):
        self.data.append(("start", tag, attrs))

    def handle_endtag(self, tag):
        self.data.append(("end", tag))

    def handle_data(self, data):
        self.data.append(("data", data))


def reconstruct_table(data):
    iterable = iter(data)
    row = next(iterable)
    while row[:2] != ('start', 'tr'):
        row = next(iterable)
    data = []
    while True:
        try:
            data.append(get_row(iterable))
        except StopIteration:
            break
    obj = [
        row for row in data
        if row
        and len(row) > 1
        and row[:2] != ('start', 'tr')
    ]
    return dict(obj)


def get_row(iterable):
    data = []
    row = next(iterable)
    while row[:2] != ('start', 'tr'):
        if row[0] == 'data':
            data.append(row[1])
        row = next(iterable)
    return data


def parse_table(string):
    p = StupidHTMLParser()
    p.feed(string)
    p.close()
    return reconstruct_table(p.data)


mapping = {
    'Consumption_m3': "consumption",
    'Area_m2': "area",
    'Jan': "january",
    'Feb': "february",
    'Mar': "march",
    'Apr': "april",
    'May': "may",
    'Jun': "june",
    'Jul': "july",
    'Aug': "august",
    'Sep': "september",
    'Oct': "october",
    'Nov': "november",
    'Dec': "december",
    'Annual agri': "annual_agriculture",
    'Annual non-agri': "annual_non_agriculture",
}

fields = {
    "consumption": "float",
    "area": "float",
    "january": "float",
    "february": "float",
    "march": "float",
    "april": "float",
    "may": "float",
    "june": "float",
    "july": "float",
    "august": "float",
    "september": "float",
    "october": "float",
    "november": "float",
    "december": "float",
    "annual_agriculture": "float",
    "annual_non_agriculture": "float",
}

def new_properties(feature):
    table = {
        mapping[k]: None if v in (-9999, '-9999') else float(v)
        for k, v in parse_table(feature['properties']['description']).items()
        if k in mapping
    }
    feature['properties'] = table
    return feature


with fiona.open("aware_prelim.gpkg", 'r') as source:
    sink_schema = source.schema.copy()
    sink_schema['geometry'] = 'MultiPolygon'
    sink_schema['properties'] = fields

    with fiona.open(
                'aware.gpkg', 'w',
                crs=source.crs,
                driver=source.driver,
                schema=sink_schema,
            ) as sink:

        for feature in source:
            sink.write(new_properties(feature))
