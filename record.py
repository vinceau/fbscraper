import os
import errno

try:
    from urllib import urlopen
    from urlparse import urlparse
    import unicodecsv as csv
except ImportError:
    from urllib.request import urlopen
    from urllib.parse import urlparse
    import csv


class FolderCreationError(Exception):
    pass


class BrokenImageError(Exception):
    pass


def make_path(path):
    """Ensures all the folders in path exists.
    Raises FolderCreationError if failed to create the required folders.
    """
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST or not os.path.isdir(path):
            raise FolderCreationError('Failed to create folder <{}>'.format(path))


class Record(object):

    def __init__(self, filename, schema):
        self.filename = filename + '.csv'
        #if there's a folder in the filename make sure it exists
        if (os.path.dirname(self.filename)):
            make_path(os.path.dirname(self.filename))
        self.file = open(self.filename, 'w')
        self.writer = csv.DictWriter(self.file, fieldnames=schema)
        self.writer.writeheader()

    def __del__(self):
        self.file.close()

    def add_record(self, data):
        self.writer.writerow(data)


class Album(object):

    def __init__(self, name, descriptions=False):
        make_path(name)
        self.name = name
        self.record = None
        if descriptions:
            self.record = Record(name, ['filename', 'description', 'permalink'])

    def add_image(self, url):
        img_bin = urlopen(url).read()
        if not img_bin:
            raise BrokenImageError
        filename = urlparse(url).path.split('/')[-1]
        fullpath = os.path.join(self.name, filename)
        with open(fullpath, 'wb') as f:
            f.write(img_bin)

    def add_description(self, imgurl, desc, perma):
        if self.record:
            filename = urlparse(imgurl).path.split('/')[-1]
            self.record.add_record({
                'filename': filename,
                'description': desc,
                'permalink': perma,
            })
