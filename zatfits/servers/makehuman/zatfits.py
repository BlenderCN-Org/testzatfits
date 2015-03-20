
import os

from core import G
from server import ZTServer

from ZTControler import ZTControler


def init(mhmain):
    ''' Called after Makehuman finished loading. '''
    controler = ZTControler(mhmain)
    try:
        controler.run()
    except Exception as e:
        print('Error during run :')
        print(str(e))
        exit()
    exit()
