
from logging import info

class itemTarget:
    '''
    Defines a measure
    '''
    def __init__(self, _increment, _decrement, _miniter, _maxiter, _accuracy, _units, folder):
        self.miniter = _miniter
        self.maxiter = _maxiter
        self.initialmaxiter = _maxiter
        self.initialminiter = _miniter
        self.accuracy = _accuracy
        self.units = _units
        self.folder = 'data/targets/%s/' % folder
        self.increment = self.folder + _increment
        self.decrement = self.folder + _decrement

class TargetNomenclature:
      '''
      Contains the nomenclature of measures (associated target, max/min value of emulated slider,
      measure accuracy (%) and unit system)
      '''
      def __init__(self):
          self.nomenclature = {}
          # Template for nomenclature, add diferents targets for every user's measure
          # self.nomenclature[measure_name] = itemTarget(measure_name_increment, measure_name_decrement, _miniter, _maxiter, _accuracy, _units)
          self.nomenclature['ARM_UPPER_LEFT_LENGTH'] = itemTarget('l-upperarm-scale-depth-incr.target', 'l-upperarm-scale-depth-decr.target', 0., 1., 0.2, 'metric', 'armslegs')
          self.nomenclature['SHOULDER_DISTANCE'] = itemTarget('torso-scale-horiz-incr.target', 'torso-scale-horiz-decr.target', 0., 1., 0.2, 'metric', 'torso')
          self.nomenclature['BUST_UNDER'] = itemTarget('torso-scale-depth-incr.target', 'torso-scale-depth-decr.target', 0., 1., 1., 'metric', 'torso')
          self.nomenclature['BUST'] = itemTarget('measure-bust-increase.target', 'measure-bust-decrease.target', -1., 1., .01, 'metric', 'measure')
          # TO ADD - Rest of nomenclatures


      def getIncrement(self, name):
          return self.nomenclature[name].increment

      def getDecrement(self, name):
          return self.nomenclature[name].decrement

      def getMin(self, name):
          return self.nomenclature[name].miniter

      def getMax(self, name):
          return self.nomenclature[name].maxiter

      def getAccuracy(self, name):
          return self.nomenclature[name].accuracy

      def getUnits(self, name):
          return self.nomenclature[name].units
