#! /usr/bin/python
# -*- coding: utf-8 -*-
# ZatFits
# Wed 16 Apr

import importlib
from ZTmeasuretarget import ZTMeasureTarget
import time


class ZThuman:
    '''
    Implementing ZatFits version of human.
    This class will directly use MH version of human class.
    /!\ THIS IS NOT MADE for app.selectedHuman /!\
    '''

    def __init__(self, h, app, key):
        self.containedHuman = h
        self.app = app
        self.key = key
        self.associate_dict = {'hip': ('hip-scale-vert-decr', 'hip-scale-vert-incr')}
        self.targetlist = []

    def __str__(self):
        return 'Human [%s]' % self.key

    def __repr__(self):
        return self.__str__()

    def save(self, path):
        self.app.saveHuman(path, self.containedHuman)

    def associate(self, target):
        return self.associate_dict[target]

    def modify(self, modification_list):
        # Instantiate the humanmodifier
        if self.app.humanmodifier is None:
            self.app.humanmodifier = importlib.import_module('humanmodifier')

        # Getting modifications from json
        if modification_list:
            for modification in modification_list:
                new_target = ZTMeasureTarget(self.app,
                                             name=modification['target'],
                                             value=float(modification['value']))
                self.targetlist.append(new_target)
        self.containedHuman.applyAllTargets()

        # Preliminary measurements
        allisMeasured = 0.
        for target in self.targetlist:
            target.measure = self.app.ztruler.getMeasure(self.containedHuman,
                                                         target.name,
                                                         target.units)
            allisMeasured += target.compareMeasureTarget()

        # Dicotomy loop
        iteration = 0
        while allisMeasured != 0.:
            dicotomystarttime = time.time()
            for target in self.targetlist:
                if target.isMeasureInferiorToValue():
                    target.miniter = target.iterval
                    target.setIter()
                    target.setModifierIter(target.iterval)
                elif target.isMeasureSuperiorToValue():
                    target.maxiter = target.iterval
                    target.setIter()
                    target.setModifierIter(target.iterval)
                else:
                    target.goal = 0.
            self.containedHuman.applyAllTargets(update=True)

            dicotomyendtime = time.time()
            iteration = iteration + 1
            t = dicotomyendtime - dicotomystarttime
            print(t)
            # requests measurements
            allisMeasured = 0.
            for target in self.targetlist:
                target.measure = self.app.ztruler.getMeasure(self.containedHuman,
                                                             target.name,
                                                             target.units)
                if abs(target.iterval) > (target.initial_max_iter - 0.001)\
                or abs(target.iterval) < (target.initial_min_iter + 0.001):
                    r = 0.
                else:
                    r = target.compareMeasureTarget()

                if r == 0:
                    allisMeasured += r
