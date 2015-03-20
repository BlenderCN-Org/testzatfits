#! /usr/bin/python
# -*- coding: utf-8 -*-
# ZatFits
# Wed 16 Apr

import os
try:
    os.remove('/tmp/ztscript.log')
except:
    pass

# Importing External librairies first
import sys
import json

# then makehuman
from makehuman import set_sys_path
# set given path the same way MakeHuman does
set_sys_path()

# We need to import human otherwise the script will throw an error,
# I havn't figured out why yet...
import human
from core import G


def main():
    app = G.app
    h = app.createHuman('test')
    app.focusHuman('test')
    j = json.dumps([{'target': 'ARM_UPPER_LEFT_LENGTH', 'value': 10.},
                    {'target': 'SHOULDER_DISTANCE', 'value': 40.}])
    v = json.loads(j)
    app.modifyHuman(v)
    app.setAge(1)
    app.saveOBJ('test')

if __name__ == '__main__':
    main()
    print('done !')
