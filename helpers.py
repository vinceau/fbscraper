from datetime import datetime

try:
    from urlparse import urljoin, urlparse, parse_qs
except ImportError:
    from urllib.parse import urljoin, urlparse, parse_qs

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


"""Takes a Facebook profile URL and extracts the user identifier whether that be an ID or a username.
Returns None if the URL is invalid.
"""
def extract_user(url):
    res = urlparse(url)
    #handle user IDs
    if res.path == '/profile.php':
        userid = parse_qs(res.query)['id']
        if len(userid) == 1:
            return userid[0]
    #handle usernames
    elif res.scheme and res.netloc:
        return res.path[1:]

    #invalid url
    return None
