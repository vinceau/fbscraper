import logging as log
import os
import errno

from threading import Thread

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
        # if there's a folder in the filename make sure it exists
        if (os.path.dirname(self.filename)):
            make_path(os.path.dirname(self.filename))
        self.file = open(self.filename, 'w')
        self.writer = csv.DictWriter(self.file, fieldnames=schema)
        self.writer.writeheader()
        log.info('Created a new record file at: %s', self.filename)

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
        Thread(target=self._image_dl(url), args=(url)).start()

    def _image_dl(self, url):
        try:
            img_bin = urlopen(url).read()
            if img_bin:
                filename = urlparse(url).path.split('/')[-1]
                fullpath = os.path.join(self.name, filename)
                with open(fullpath, 'wb') as f:
                    f.write(img_bin)
            return
        except IOError:
            # there was some issue with the connection
            # raise the Broken Image Error
            pass
        raise BrokenImageError


    def add_description(self, imgurl, desc, perma):
        if self.record:
            filename = urlparse(imgurl).path.split('/')[-1]
            self.record.add_record({
                'filename': filename,
                'description': desc,
                'permalink': perma,
            })
