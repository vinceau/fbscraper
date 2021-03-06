from datetime import datetime

try:
    from urlparse import urljoin, urlparse, parse_qs
except ImportError:
    from urllib.parse import urljoin, urlparse, parse_qs


def join_url(base, query):
    """Joins a query to a url.
    """
    sep = '&' if '?'in base else '?'
    return base + sep + query


def strip_query(url):
    """Strips the query portion of a url if it doesn't contain 'profile.php'
    """
    if 'profile.php' not in url:
        return urljoin(url, urlparse(url).path)
    return url


def timestring(unix=None):
    """Converts a unix time stamp into a human readable timestamp.
    If no time stamp is provided it gives the current time.
    """
    timeformat = "%Y%m%d-%H%M%S"
    if unix:
        return datetime.fromtimestamp(int(unix)).strftime(timeformat)
    return datetime.now().strftime(timeformat)


def path_safe(path):
    """Makes a path a bit safer by replacing the unsafe characters found in unsafe_char with '-'.
    """
    # replace the unsafe characters with replacement
    unsafe_chars = [' ', '/', '\\']
    replacement = '-'
    new_path = path
    for c in unsafe_chars:
        new_path = new_path.replace(c, replacement)
    return new_path.strip(replacement)


def get_targeturl(target):
    """Given a target, returns the target URL. If target is a URL just return target.
    Not guaranteed to be accurate since usernames could also be fully numbers (I think).
    """
    # target is a URL
    if get_target(target) is not None:
        return target

    # target is not a URl
    if target.isdigit():
        return 'https://www.facebook.com/profile.php?id=' + target
    else:
        return 'https://www.facebook.com/' + target


def get_target(targeturl):
    """Takes a Facebook profile URL and extracts the user identifier whether that be an ID or a username.
    Returns None if the URL is invalid.
    """
    res = urlparse(targeturl)
    # handle user IDs
    if res.path == '/profile.php':
        userid = parse_qs(res.query)['id']
        if len(userid) == 1:
            return userid[0]
    # handle usernames
    elif res.scheme and res.netloc:
        return res.path[1:]

    # invalid url
    return None
