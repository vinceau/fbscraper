
from datetime import datetime
from urlparse import urljoin, urlparse

unsafe_chars = [' ', '/', '\\']

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


"""Makes a path a bit safer by replacing the unsafe characters found in unsafe_char with '-'.
"""
def path_safe(path):
    new_path = path
    for c in unsafe_chars:
        new_path = new_path.replace(c, '-')
    return new_path
