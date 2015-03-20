#!/usr/bin/python
# -*- coding: utf-8 -*-
# ZatFits
# Wed 16 Apr

from logging import basicConfig as LoggingSetup, DEBUG, info
import time
import os
import importlib
import math
import json

import algos3d
import human
import files3d
from ZThuman import ZThuman
from ZTmeasuretarget import ZTMeasureTarget
from ZTtargetnomenclature import TargetNomenclature
from ZTfilereader import ZTFileReader as ZTFR


class ZTRuler:

    def __init__(self):
        self.ztmeasures = {}
        # loading nomenclatures from nomenclature.json
        self.ztmeasures = json.loads(str(ZTFR('ZTdata/nomenclatures.json')))


    def getMeasure(self, human, measurementname, mode='metric'):
        measure = 0.
        vindex1 = self.ztmeasures[measurementname][0]
        for vindex2 in self.ztmeasures[measurementname]:
            vec = human.meshData.coord[vindex1] - human.meshData.coord[vindex2]
            measure += math.sqrt(vec.dot(vec))
            vindex1 = vindex2
        if mode == 'metric':
            return 10.0 * measure
        else:
            return 10.0 * measure * 0.393700787


class App():
    '''
    App class which is used in lib/core.py
    to fake app content with zatfits
    '''

    # MH uses a notion of selected_human for its
    # operations, this is the one we provide
    selectedHuman = None
    ZTselectedHuman = None

    # A dictionary of humans per Makehuman instance
    ZThumans = {}

    exportutils = None
    wavefront = None
    humanmodifier = None
    ztruler = ZTRuler()
    zttargetnomenclature = TargetNomenclature()
    targetlist = []
    progress = None

    saveHandlers = {}

    def __init__(self):
        LoggingSetup(filename='/tmp/ztscript.log', level=DEBUG)

    def loadMacroTargets(self, human):
        '''
        Preload all target files belonging to group macrodetails and its child
        groups.
        '''
        import targets
        #import getpath
        print('Loading macroTargets :')
        i = 0
        for target in targets.getTargets().findTargets('macrodetails'):
            print('\t%s' % target.path)
            #log.debug('Preloading target %s', getpath.getRelativePath(target.path))
            algos3d.getTarget(human.meshData, target.path)
            i = i +1
        print('Properly loaded %d macroTargets' % i)

    def createHuman(self, key, model='base.npz'):
        '''
        Creates a Human model and adds it to
        self.selected_humans[key],
        models are stored in data/3dobjs/
        '''
        model_path = './data/3dobjs/%s' % model
        h = human.Human(files3d.loadMesh(model_path,
                                         maxFaces=5))
        self.ZThumans[key] = ZThuman(h, self, key)
        self.loadMacroTargets(h)
        h.applyAllTargets()
        return self.ZThumans[key]

    def addSaveHandler(save, handler, priority=None):
        if priority is None:
            self.saveHandlers.append(handler)
        else:
            self.saveHandlers.insert(priority, handler)

    def saveMHM(self, filename, h=None):
        h = self.selectedHuman if h is None else h
        if self.exportutils is None:
            self.exportutils = importlib.import_module('exportutils')
        if self.wavefront is None:
            self.wavefront = importlib.import_module('wavefront')
        if not filename.lower().endswith('.mhm'):
            filename += '.mhm'
        self.selectedHuman.save(filename, filename)

    def saveOBJ(self, path, h=None):
        h = self.selectedHuman if h is None else h
        # here i'm importing wavefront and exportutils dynamicly forcing it to
        # execute after global initialisation. Causes errors otherwise.
        # Still i didn't want to import these modules everytime the method was
        # called so I stores them in the class instance of the app.
        if self.exportutils is None:
            self.exportutils = importlib.import_module('exportutils')
        if self.wavefront is None:
            self.wavefront = importlib.import_module('wavefront')

        # normal save process from here..
        config = self.exportutils.config.Config()
        config.setHuman(h)
        config.setupTexFolder(path)
        filename = os.path.basename(path)
        name = config.goodName(os.path.splitext(filename)[0])
        tmp = config.subdivide
        rmeshes = self.exportutils.collect.setupMeshes(name,
                                                       h,
                                                       config=config,
                                                       subdivide=tmp)
        objects = [rmesh.object for rmesh in rmeshes]

        # seting False as last parameter on writeObjFile will write
        # the OBJ file,
        # setting True will write the NML file
        self.wavefront.writeObjFile('%s.obj' % path, objects, False)
        self.wavefront.writeObjFile('%s.nml' % path, objects, True)

    def load(self, h, key):
        zthuman = ZThuman(h, self, key)
        self.ZThumans[key] = zthuman

    def focusHuman(self, key):
        if key not in self.ZThumans:
            return False
        else:
            self.selectedHuman = self.ZThumans[key].containedHuman
            self.ZTselectedHuman = self.ZThumans[key]

    def setGender(self, gender):
        ''' Set the gender of the current human,
            0 is femal, 1 is male.

            Parameters
            ----------

            amount:
                *float*. An amount, usually between 0 and 1, specifying how much
                of the attribute to apply.
        '''
        self.selectedHuman.setGender(gender)


    def getGender(self):
        return self.selectedHuman.gender


    def setAge(self, age):
        '''
        Sets the age of the model. 0 for 0 years old, 1 is 70. To set a
        particular age in years, use the formula age_value = age_in_years / 70.

        Parameters
        ----------

        amount:
            *float*. An amount, usually between 0 and 1, specifying how much
            of the attribute to apply.
        '''
        self.selectedHuman.setAge(age)

    def getAge(self):
        return self.selectedHuman.age

    def setWeight(self, weight):
        '''
        Sets the amount of weight of the model. 0 for underweight, 1 for heavy.

        Parameters
        ----------

        amount:
            *float*. An amount, usually between 0 and 1, specifying how much
            of the attribute to apply.
        '''
        self.selectedHuman.setWeight(weight)

    def getWeight(self):
        return self.selected.weight

    def setMuscle(self, muscle):
        '''
        Sets the amount of muscle of the model. 0 for flacid, 1 for muscular.

        Parameters
        ----------

        amount:
            *float*. An amount, usually between 0 and 1, specifying how much
            of the attribute to apply.
        '''
        self.selectedHuman.setMuscle(muscle)

    def getMuscle(self):
        return self.selectedHuman.getMuscle()

    def setHeight(self, height):
        self.selectedHuman.setHeight(height)

    def getHeight(self):
        return self.selectedHuman.getHeight()

    def setCaucasian(self, caucasian):
        self.selectedHuman.setCaucasian(caucasian)

    def getCaucasian(self):
        return self.selectedHuman.getCaucasian()

    def setAfrican(self, african):
        self.selectedHuman.setAfrican(african)

    def getAfrican(self):
        return self.selectedHuman.getAfrican()

    def setAsian(self, asian):
        self.selectedHuman.setAsian(asian)

    def getAsian(self):
        return self.selectedHuman.getAsian()

    def modifyHuman(self, modification_list):
        '''
        Modifies the selected human with selected modification_list.
        '''
        self.ZTselectedHuman.modify(modification_list)

