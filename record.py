import csv
import os

from urllib.request import urlopen
from urllib.parse import urlparse

class FolderCreationError(Exception):
    pass

class BrokenImageError(Exception):
    pass


class Record(object):

    def __init__(self, filename, schema):
        self.filename = filename + '.csv'
        if (os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        self.file = open(self.filename, 'w')
        self.writer = csv.DictWriter(self.file, fieldnames=schema)
        self.writer.writeheader()

    def __del__(self):
        self.file.close()

    def add_record(self, data):
        self.writer.writerow(data)


class Album(object):

    def __init__(self, name):
        try:
            os.makedirs(name, exist_ok=True)
            self.name = name
        except OSError:
            if not os.path.isdir(name):
                #error making directory
                raise FolderCreationError('Failed to create folder <{}>'.format(name))

    def add_image(self, url):
        img_bin = urlopen(url).read()
        if not img_bin:
            raise BrokenImageError
        filename = urlparse(url).path.split('/')[-1]
        fullpath = os.path.join(self.name, filename)
        with open(fullpath, 'wb') as f:
            f.write(img_bin)

