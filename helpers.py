
from datetime import datetime
from urlparse import urljoin, urlparse

"""Joins a query to a url.
"""
def join_url(base, query):
    sep = '&' if '?'in base else '?'
    return base + sep + query

"""Strips the query portion of a url if it doesn't contain 'profile.php'
"""
def strip_query(url):
    if 'profile.php' not in url:
        return urljoin(url, urlparse(url).path)
    return url

"""Converts a unix time stamp into a human readable timestamp.
If no time stamp is provided it gives the current time.
"""
def timestring(unix=None):
    timeformat = "%Y%m%d-%H%M%S"
    if unix:
        return datetime.fromtimestamp(int(unix)).strftime(timeformat)
    return datetime.now().strftime(timeformat)


