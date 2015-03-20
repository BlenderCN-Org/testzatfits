#!/usr/bin/python
# -*- coding: utf-8 -*-
# ZatFits
# Wed 21 May

import math
import os
import json
import time

import sys

import humanmodifier

import exportutils
import wavefront

from ZTmeasuretarget import ZTMeasureTarget
from ZTtargetnomenclature import TargetNomenclature
from ZTfilereader import ZTFileReader as ZTFR
from ZTserver import ZTServer
from socket import SHUT_RDWR
import ZTDaeUtils
import codecs

mypath_ZT = os.environ['ZTPATH']

from re import compile as Rgc


class ZTExportUtils:

    def __init__(self, mhmain):
        self._mhmain = mhmain

    def exportOBJ(self, path):
        h = self._mhmain.selectedHuman
        # here i'm importing wavefront and exportutils dynamicly forcing it to
        # execute after global initialisation. Causes errors otherwise.
        # Still i didn't want to import these modules everytime the method was
        # called so I stores them in the class instance of the app.
        # normal save process from here..
        config = exportutils.config.Config()
        config.setHuman(h)
        config.setupTexFolder(path)
        filename = os.path.basename(path)
        name = config.goodName(os.path.splitext(filename)[0])
        tmp = config.subdivide
        rmeshes = exportutils.collect.setupMeshes(name,
                                                  h,
                                                  config=config,
                                                  subdivide=tmp)
        objects = [rmesh.object for rmesh in rmeshes]

        # seting False as last parameter on writeObjFile will write
        # the OBJ file,
        # setting True will write the NML file
        wavefront.writeObjFile('%s.obj' % path, objects, False,config)
        wavefront.writeObjFile('%s.mtl' % path, objects, True,config)

    def exportDAE(self, path) :
        from armature.armature import setupArmature
        print 'Path for stock model : ' + path
        h = self._mhmain.selectedHuman
        config = ZTDaeUtils.ZTDaeConfig()
        config.setHuman(h)
        config.setupTexFolder(path)
        filename = os.path.basename(path)
        name = config.goodName(os.path.splitext(filename)[0])
        tmp = config.subdivide

        amt = setupArmature(name, h, config.rigOptions)
        rawTargets = exportutils.collect.readTargets(h, config)
        rmeshes = exportutils.collect.setupMeshes(
        name,
        h,
        amt=amt,
        config=config,
        subdivide=tmp,
        rawTargets = rawTargets)

        try:

            try:
                fp = codecs.open('%s.dae' % path, 'w', encoding="utf-8")
            except:
				print ('Error at open file : %s' %path) 
				fp = None

            date = time.strftime(u"%a, %d %b %Y %H:%M:%S +0000".encode('utf-8'), time.localtime()).decode('utf-8')
            if config.yUpFaceZ or config.yUpFaceX:
                upvector = "Y_UP"
            else:
                upvector = "Z_UP"
            fp.write('<?xml version="1.0" encoding="utf-8"?>\n' +
                '<COLLADA version="1.4.0" xmlns="http://www.collada.org/2005/11/COLLADASchema">\n' +
                '  <asset>\n' +
                '    <contributor>\n' +
                '      <author>www.makehuman.org</author>\n' +
                '    </contributor>\n' +
                '    <created>%s</created>\n' % date +
                '    <modified>%s</modified>\n' % date +
                '    <unit meter="%.4f" name="%s"/>\n' % (0.1/config.scale, config.unit) +
                '    <up_axis>%s</up_axis>\n' % upvector +
                '  </asset>\n')

            ZTDaeUtils.writeLibraryImages(fp, rmeshes, config)

            ZTDaeUtils.writeLibraryEffects(fp, rmeshes, config)

            ZTDaeUtils.writeLibraryMaterials(fp, rmeshes, config)

            ZTDaeUtils.writeLibraryControllers(fp, rmeshes, amt, config)

            ZTDaeUtils.writeLibraryGeometry(fp, rmeshes, config)

            ZTDaeUtils.writeLibraryVisualScenes(fp, rmeshes, amt, config)

            fp.write(
                '  <scene>\n' +
                '    <instance_visual_scene url="#Scene"/>\n' +
                '  </scene>\n' +
                '</COLLADA>\n')

        finally:
            if fp:
                fp.close()

    def exportMHM(self, path):
        filename = path[path.find('/') + 1:]
        self._mhmain.selectedHuman.save(path, filename)

    def loadMHM(self, path):
        self._mhmain.selectedHuman.load(path)

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


class ZTModifyUtils:

    def __init__(self, mhmain):
        self._mhmain = mhmain
        self.zttargetnomenclature = TargetNomenclature()
        self.ztruler = ZTRuler()

    # SETTERS

    def setJSONModify(self, json_modifications):
        ''' Human modifier by dichotomy. Takes a JSON list of modifications '''

        targetlist = []

        # Getting modifications from json
        if json_modifications:
            for modification in json_modifications:
                new_target = ZTMeasureTarget(self.zttargetnomenclature,
                                             self._mhmain.selectedHuman,
                                             name=modification['target'],
                                             value=float(modification['value']))
                targetlist.append(new_target)
        self._mhmain.selectedHuman.applyAllTargets()

        # Preliminary measurements
        allisMeasured = 0.
        for target in targetlist:
            target.measure = self.ztruler.getMeasure(self._mhmain.selectedHuman,
                                                         target.name,
                                                         target.units)

            allisMeasured += target.compareMeasureTarget()


       # Dicotomy loop
        iteration = 0
        print "Enter in Loop"
        while allisMeasured != 0.:
            dicotomystarttime = time.time()
            for target in targetlist:
                if target.isMeasureInferiorToValue():
                    target.miniter = target.iterval
                    target.setIter()
                    print "Inf"
                    print target.iterval
                    target.setModifierIter(target.iterval)
                elif target.isMeasureSuperiorToValue():
                    target.maxiter = target.iterval
                    target.setIter()
                    print "Sup"
                    print target.iterval
                    target.setModifierIter(target.iterval)
                else:
                    target.goal = 0.
            self._mhmain.selectedHuman.applyAllTargets(update=True)

            dicotomyendtime = time.time()
            iteration = iteration + 1
            t = dicotomyendtime - dicotomystarttime
           # print(t)
            # requests measurements
            allisMeasured = 0.
            for target in targetlist:
                target.measure = self.ztruler.getMeasure(self._mhmain.selectedHuman,
                                                             target.name,
                                                             target.units)
                if abs(target.iterval) > (target.initial_max_iter - 0.001)\
                or abs(target.iterval) < (target.initial_min_iter + 0.001):
                    r = 0.
                else:
                    r = target.compareMeasureTarget()
                    print 'valeur de  r'
                    print r

                if r <> 0:
                    allisMeasured += r
                    print 'valeur de  r'
                    print r
            for target in targetlist:
                target.measure = self.ztruler.getMeasure(self._mhmain.selectedHuman,
                                                             target.name,
                                                             target.units)
            print target.name
            print target.measure



    def getJSONValue(self, json_modifications):
        ''' Human modifier by dichotomy. Takes a JSON list of modifications '''

        targetlist = []

        # Getting modifications from json
        try:
            if json_modifications:
                for modification in json_modifications:
                    new_target = ZTMeasureTarget(self.zttargetnomenclature,
                                                 self._mhmain.selectedHuman,
                                                 name=modification['target'],
                                                 value=float(modification['value']))
                    targetlist.append(new_target)
            #self._mhmain.selectedHuman.applyAllTargets()
        except Exception as e:
            print(e)
            print('ERRORR 1')

        try:
            # Preliminary measurements
            allisMeasured = 0.
            for target in targetlist:
                target.measure = self.ztruler.getMeasure(self._mhmain.selectedHuman,
                                                             target.name,
                                                             target.units)
                allisMeasured += target.compareMeasureTarget()
            print target.name + " : " + str(target.measure)
        except:
            print('ERROR 2')

        return target.measure

    def setBodyBasic(self, metric, gender, age, height, bust, weight, muscle):

        print 'gender' + str(gender)
        print 'metric' + str(metric)
        print 'age' + str(age)
        print 'height' + str(height)
        print 'bust' + str(bust)
        print 'weight' + str(weight)
        print 'muscle' + str(muscle)

        # Here we set the parameter values (extracted from the json in generate()) to the wanted values
        # If the value is set at -1000 then it wasnt input by the user and must be set to a default value
        # Keep in mind that when values are extracted they can be in metric or imperial units and when they need to
        #   be converted to a value between 0 and 1 the min and max values possible must coincide with those of the
        #   XML file. ex: self.setWeight(weight*1/180) works with max= 180 of the XML file
        self.setGender(gender)

        if(age==-1000):
            self.setAgeYears(35)
        else:
            self.setAgeYears(age)

        if(height==-1000):
        #set height in Cm
            self.setHeight(175)
        elif (metric==1):
            self.setHeight(height)
        else:
            self.setHeight(height*2.54)

        if(weight==-1000):
            self.setWeight(0.5)
        elif(metric==1):
            self.setWeight(weight*1/180)
        else:
            self.setWeight(weight*0.45359237/180)

        if(muscle==-1000):
            self.setMuscle(0.5)
        else:
            self.setMuscle(muscle/100)

        #pas oublier accurate
        accurate=0.1
        loop=0

        min=0
        max=1
        iter=(max+min)/2.
        self.setHeight(iter)
        measure=self.getHeightCm()

        while(abs(height-measure)>accurate):

            if  (height-measure)>0:
                min=iter
                iter=(max+min)/2.
            else:
                max=iter
                iter=(max+min)/2.
            self.setHeight(iter)
            measure=self.getHeightCm()

            if abs(iter)>0.9999:
                break
            if abs(iter)<0.0001:
                break



        j = json.dumps([{'target': 'BUST', 'value': bust}])
        v = json.loads(j)


        if gender == 0:
            min=0
            max=1
            iter=(max+min)/2.
            self.setBreastSize(iter)
            measure=self.getJSONValue(v)

            while(abs(bust-measure)>accurate):

                if  (bust-measure)>0:
                    min=iter
                    iter=(max+min)/2.
                else:
                    max=iter
                    iter=(max+min)/2.
                self.setBreastSize(iter)
                measure=self.getJSONValue(v)
                if loop>50:
                    break
                if abs(iter)>0.9999:
                    break
                if abs(iter)<0.0001:
                    break
        else :
            self.setJSONModify(v)


        return iter




    def setGender(self, gender):
        ''' Set the gender of the current human,
            0 is femal, 1 is male.

            Parameters
            ----------

            amount:
                *float*. An amount, usually between 0 and 1, specifying how much
                of the attribute to apply.
        '''
        self._mhmain.selectedHuman.setGender(gender)

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
        self._mhmain.selectedHuman.setAge(age)

    def setAgeYears(self, age):
        self._mhmain.selectedHuman.setAgeYears(age)

    def setBreastSize(self, size):
        '''
        Sets the breast size of the model.

        Parameters
        ----------

        amount:
            *float*. An amount, usually between 0 and 1, specifying how much
            of the attribute to apply.
        '''
        self._mhmain.selectedHuman.setBreastSize(size)





    def setWeight(self, weight):
        '''
        Sets the amount of weight of the model. 0 for underweight, 1 for heavy.

        Parameters
        ----------

        amount:
            *float*. An amount, usually between 0 and 1, specifying how much
            of the attribute to apply.
        '''
        self._mhmain.selectedHuman.setWeight(weight)

    def setMuscle(self, muscle):
        '''
        Sets the amount of muscle of the model. 0 for flacid, 1 for muscular.

        Parameters.staticFaceMask
        ----------

        amount:
            *float*. An amount, usually between 0 and 1, specifying how much
            of the attribute to apply.
        '''
        self._mhmain.selectedHuman.setMuscle(muscle)

    def setAsian(self, asian):
        self._mhmain.selectedHuman.setAsian(asian)

    def setCaucasian(self, caucasian):
        self._mhmain.selectedHuman.setCaucasian(caucasian)

    def setAfrican(self, african):
        self._mhmain.selectedHuman.setAfrican(african)

    def getMuscle(self):
        return self._mhmain.selectedHuman.getMuscle()

    def setHeight(self, height):
        self._mhmain.selectedHuman.setHeight(height)

    def load (self, filename):
        self._mhmain.selectedHuman.load(filename)

    # GETTERS

    def getHeight(self):
        return self._mhmain.selectedHuman.getHeight()

    def getHeightCm(self):
        """
        The height in cm.
        """
        return self._mhmain.selectedHuman.getHeightCm()


    def getAfrican(self):
        return self._mhmain.selectedHuman.getAfrican()

    def getAsian(self):
        return self._mhmain.selectedHuman.getAsian()

    def getGender(self):
        return self._mhmain.selectedHuman.gender

    def getAge(self):
        return self._mhmain.selectedHuman.age

    def getAgeYears(self):
        return self._mhmain.selectedHuman.getAgeYears()

    def getWeight(self):
        return self._mhmain.selectedHuman.weight

    def getCaucasian(self):
        return self._mhmain.selectedHuman.getCaucasian()

class ZTControler:

    def __init__(self, mhmain):
        self._m = mhmain
        self.exportutils = ZTExportUtils(self._m)
        self.modifyutils = ZTModifyUtils(self._m)
        self.protocol = [(Rgc('^generate'), self.generate),
                         (Rgc('^check'), self.check),
                         (Rgc('^exit'), self.exit)]

    def exit(self, msg):
        for socket in self.net._sockets:
            try:
                socket.shutdown(SHUT_RDWR)
                socket.close()
            except Exception as e:
                print('socket closing error %s' % str(e))
        # self.net._listeningSock.shutdown()
        self.net._listeningSock.close()
        print('Bye bye !')
        sys.exit()

    def check(self, msg):
        '''
        Check status
        '''
        msg[1].send('O.K')

    def generate(self, msg):
        '''
        Authenticate method. Used by the dispatcher for every new user
        connection
        '''
        # self.modifyutils.agedyBasic(gender,age,height,value_bust)
        name = 'TEST'
        data_json = json.loads(msg[0][msg[0].find(':') + 1:])
        data = {}
        for key, value in data_json:
            data[key] = value
        self.modifyutils.setBodyBasic(int(data['Metric']),
                                      int(data['Gender']),
                                      int(data['Age']),
                                      float(data['Size']),
                                      float(data['Buste']),
                                      float(data['Weight']),
                                      float(data['Muscle']))
        try:
	    print 'Export Data User: ' + str(data['user'])
            #self.exportutils.exportOBJ('/home/vanmeer/testGit/Zatfits/media/%s' % data['user'])
            #self.exportutils.exportMHM('/home/vanmeer/testGit/Zatfits/media/%s.mhm' % data['user'])
            self.exportutils.exportDAE( mypath_ZT + '/zatfits/user_models/%s/'%data['user']+'%s'%data['user'])
        except Exception as e:
            print(e)
        msg[1].send(str(data['user']))
        #msg[1].send('O.K')
	
    def execute(self, msg):
        for cmd in self.protocol:
            rcd = msg[0]
            if ':' in rcd:
                rcd = rcd[:rcd.find(':')]
            if cmd[0].match(rcd):
                cmd[1](msg)

    def run(self):
        '''
        Called after makehuman loading and ZTControler initialisation.

        This is basicly a the MAIN
        '''
        print('New Makehuman server given %s as parameter' % sys.argv)
        s = ZTServer(int(sys.argv[1]), verbose=True)
        self.net = s
        while True:
            s.Iterate()
            new_messages = s.Received()
            if new_messages:
                for msg in new_messages:
                    self.execute(msg)
