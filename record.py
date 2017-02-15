import unicodecsv as csv


class Record(object):

    def __init__(self, filename, schema):
        self.filename = filename + '.csv'
        self.file = open(self.filename, 'w')
        self.writer = csv.DictWriter(self.file, fieldnames=schema)
        self.writer.writeheader()

    def __del__(self):
        self.file.close()

    def add_record(self, data):
        self.writer.writerow(data)
