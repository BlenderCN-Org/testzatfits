
#!/usr/bin/python
# -*- coding: utf-8 -*-
# ZatFits
# Mon 21 Apr


class ZTFileReader():
    ''' Reads a file and gets proper str content '''

    def __init__(self, path):
        self.content = ''
        try:
            self.file = open(path)
            for line in self.file.readlines():
                self.content = self.content + line.replace('\n', '')
            self.file.close()
        except Exception as e:
            return e

    def __str__(self):
        return self.content

    def __repr__(self):
        return self.__str__()
