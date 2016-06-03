'''
machine interface
includes online optimizer, response measurement and other stuff
'''

from pylab import *
from scipy.optimize import *
import scipy.optimize as opt
from time import sleep

import json


'''
Any machine interface class should implement following methods  
'''
class MachineInterface:
    def __init__(self):
        pass
    def get_alarms(self):
        '''
        return an array of values for all active bpms
        values range between (0,1) 1 corresponds to alarm level
        '''
        pass
    def get_sase(self, detector_name='default'):
        '''
        return SASE pulse energy
        units and averaging can be arbitrary        '''

        pass
    def get_value(self, device_name):
        pass
    def set_value(self, device_name, val):
        pass
    def init_corrector_vals(self, correctors):
        pass
    

'''
placeholder for magnet field ranges etc.
'''
class DeviceProperties:
    def __init__(self):
        self.limits = [-1000, 1000]


class Optimizer:
    def __init__(self, mi, dp):
        self.debug = False
        self.mi = mi
        self.dp = dp
        self.timeout = 1.0
        self.logging = False

    def eval(self, seq, logging = False, log_file = None):
        for s in seq:
            s.apply()


    def max_sase(self,correctors, method = 'simplex', params = {}, opt_pointing = False):
        '''
        direct sase optimization with simplex, using correctors as a multiknob
        '''
        if self.debug: print 'starting multiknob optimization, correctors = ', correctors

        if opt_pointing:
            weight_gmd_bpm_1 = 10.0
            weight_gmd_bpm_2 = 10.0
        else:
            weight_gmd_bpm_1 = 0.0
            weight_gmd_bpm_2 = 0.0
    
        def error_func(x):

            print self.dp
            
            pen_max = 100.0
    
            #print 'error_func: ', bpm_names, '->',  planes
    
            for i in xrange(len(x)):
                print '{0} x[{1}]={2}'.format(correctors[i], i, x[i])
                limits = self.dp.get_limits(correctors[i])
                print  'limits=[{0}, {1}]'.format(limits[0], limits[1])
                if x[i] < limits[0] or x[i] > limits[1]:
                    print 'limits exceeded'
                    return pen_max
    
    
            for i in xrange(len(correctors)):
                print 'setting', correctors[i], '->',x[i]
                self.mi.set_value(correctors[i], x[i])
    
            sleep(self.timeout)
    
            sase = self.mi.get_sase()
            alarm = np.max(self.mi.get_alarms())
            #z1, z2 = get_sase_pos()
    
            if self.debug: print 'alarm:', alarm
            if self.debug: print 'sase:', sase
            #print 'pointing', z1, z2, 'weights', weight_gmd_bpm_1, weight_gmd_bpm_2
    
            pen = 0.0
    
            if alarm > 1.0:
                return pen_max
            if alarm > 0.7:
                return alarm * 50.0
            pen += alarm
    
            pen -= sase    

            if self.debug: print 'penalty:', pen
    
            return pen
        

        sase_ref = self.mi.get_sase()
    
        x = self.mi.init_corrector_vals(correctors)
        x_init = x

        if self.logging: 
            f = open(self.log_file,'a')
            f.write('\n*** optimization step ***\n')
            f.write(str(correctors) + '\n')
            f.write(method + '\n')
            f.write('x0=' + str(x_init) + '\n')
            f.write('sase0=' + str(sase_ref) + '\n')

        
        if method == 'cg':
            print 'using CG optimizer, params:', params 
            
            try:
                max_iter = params['maxiter']
            except KeyError:
                max_iter = 10 * len(x)

            try:
                epsilon = params['epsilon']
            except KeyError:
                epsilon = 0.1

            try:
                gtol = params['gtol']
            except KeyError:
                gtol = 1.e-3
                        
            opt.fmin_cg(error_func,x,gtol=gtol, epsilon = epsilon, maxiter=max_iter)
        
        if method == 'simplex':
            print 'using simplex optimizer, params:', params
            
            try:
                max_iter = params['maxiter']
            except KeyError:
                max_iter = 10 * len(x)

            try:
                xtol = params['xtol']
            except KeyError:
                xtol = 1.e-3

            opt.fmin(error_func,x,xtol=xtol, maxiter=max_iter)
        
        if method == 'powell': 
            print 'using powell optimizer, params:', params
            
            try:
                max_iter = params['maxiter']
            except KeyError:
                max_iter = 10 * len(x)

            try:
                xtol = params['xtol']
            except KeyError:
                xtol = 1.e-3

            opt.fmin_powell(error_func,x,xtol=xtol, maxiter=max_iter)


        if method == 'fancy_stuff_from': 
            print 'using fancy optimizer, params:', params
            pass

        sase_new = self.mi.get_sase()
        
        print 'step ended changing sase from/to', sase_ref, sase_new
        if sase_new <= sase_ref:
            for i in xrange(len(correctors)):
                print 'reverting', correctors[i], '->',x_init[i]
                self.mi.set_value(correctors[i], x_init[i])

        if self.logging:
             f.write('sase_new=' + str(sase_new) + '\n')
             f.close()



class Action:
    def __init__(self, func, args = None, id = None):
        self.func = func
        self.args = args
        self.id = id
    def apply(self):
        print 'applying...', self.id
        self.func(*self.args)
    def to_JSON(self):
        print "hoo"
    def __repr__(self):
        return json.dumps(self.__dict__)


'''
test interface
'''
class TestInterface:
    def __init__(self):
        pass
    def get_alarms(self):
        return [0.0,]
    def get_sase(self):
        return 0.0
    def init_corrector_vals(self, correctors):
        vals = [0.0]*len(correctors)
        return vals
    def get_value(self, device_name):
        return 0.0
    def set_value(self, device_name, val):
        return 0.0


'''
flight simulator implementation of the machine interface
'''
class FlightSimulator:
    def __init__(self, lattice, beam):
        self.lattice = lattice
        self.beam = beam
    def get_alarms(self):
        return 0.0
    def get_sase(self, detector_name='default'):
        return 0.0