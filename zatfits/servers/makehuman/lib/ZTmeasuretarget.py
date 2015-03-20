
from logging import info

import humanmodifier

class ZTMeasureTarget:
    '''
    The value to get and associated methods of measure
    '''
    def __init__(self, zttargetnomenclature, human, name='default', value=0.5):
        self.name = name
        self.human = human
        self.value = value
        self.zttargetnomenclature = zttargetnomenclature
        self.goal = 1.
        self.increment = "target_incr"
        self.decrement = "target_decr"
        nomenclature_target = (self.zttargetnomenclature.getDecrement(name),
                               self.zttargetnomenclature.getIncrement(name))
        self.modifier = humanmodifier.Modifier(nomenclature_target[0],
                                               nomenclature_target[1])
        self.measure = 0.
        # WARNING , this value is in %
        self.accuracy = 1.
        self.iterval = 0.
        self.initializeTargetsMinMaxUnits(self.zttargetnomenclature)
        self.initial_min_iter = self.miniter
        self.initial_max_iter = self.maxiter
        self.setIter()
        self.setHuman(self.human)
        self.setModifierIter(self.iterval)

    def setIter(self):
        self.iterval = (self.maxiter + self.miniter) / 2.

    def setHuman(self, human):
        ''' Assigning the model to the modifier '''
        self.modifier.setHuman(human)

    def setModifierIter(self, iterval):
        ''' Assigning modifier iterval '''
        self.modifier.setValue(self.iterval)

    def compareMeasureTarget(self):
        ''' Compare measure to target value '''
        if (self.isMeasureSuperiorToValue() or self.isMeasureInferiorToValue()):
            self.goal = 1.
        else:
            self.goal = 0.
        return self.goal

    def isMeasureSuperiorToValue(self):
        ''' Determines if the measure is superior to value within accuracy upper bound '''
        if (self.measure > (self.value * (100. + self.accuracy) / 100.)):
            return True
        else:
            return False

    def isMeasureInferiorToValue(self):
        ''' Determines if the measure is inferior to value within accuracy lower bound '''
        if (self.measure < (self.value * (100. - self.accuracy) / 100.)):
            return True
        else:
            return False

    def getAccuracyLowerBound(self):
        return (self.value * (100. - self.accuracy) / 100.)

    def getAccuracyUpperBound(self):
        return (self.value * (100. + self.accuracy) / 100.)

    def getDeltaMeasure(self):
        '''Calculating the gap between target value and measure '''
        return (self.measure - self.value)

    def initializeTargetsMinMaxUnits(self, targetNomenclature):
        '''
        We initialise the targets values, min, max, units and precision
        according to the target name
        '''
        self.increment = targetNomenclature.getIncrement(self.name)
        self.decrement = targetNomenclature.getDecrement(self.name)
        self.miniter = targetNomenclature.getMin(self.name)
        self.maxiter = targetNomenclature.getMax(self.name)
        self.accuracy = targetNomenclature.getAccuracy(self.name)
        self.units = targetNomenclature.getUnits(self.name)

