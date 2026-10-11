# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 09:46:06 2019

@author: user
"""
from pc_classes.polecad import PoleCalcConfig, poleCalculationClass
from pc_classes.pc_functions import dataconstants as dct

projectname='Spans'
projectdir='./PoleCadTests/'+projectname+'/'

config=PoleCalcConfig(
    project_name=projectname,
    project_dir=projectdir,
    design_tension=0.5,
    strength_factor=0.65,
    wind_load=4,
    wind_overload=2.5,
    tension_overload=1.65,
    ice_thickness=0.5,
    wind_angle=dct.eastwind,
    deflection_factor=1)

pcc=poleCalculationClass(config)
pcc.run_max_span()

#Strength Factors
#                                          B          C
#Ice & Wind (250B)                        0.65       0.85
#Extreme Wind (250C)                      1.0        1.0
#Extreme Ice with Concurrent Wind (250D)  0.75       0.75
