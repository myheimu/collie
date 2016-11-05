__author__ = 'haibin'


class Table(object):
    def __init__(self, name, description, columns):
        self.name = name
        self.description = description
        self.columns = columns


class TableOperator(object):
    def __init__(self, name):
        self.name = name
