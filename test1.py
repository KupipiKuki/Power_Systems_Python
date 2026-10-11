# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 09:46:06 2019

@author: user
"""
from pc_classes.polecad import PoleCalcConfig, poleCalculationClass
from pc_classes import powercad as pcd
from pc_classes.pc_functions import dataconstants as dct

projectname='Test1'
projectdir='./PoleCadTests/'+projectname+'/'

config=PoleCalcConfig(
    project_name=projectname,
    project_dir=projectdir,
    design_tension=0.6,
    strength_factor=0.85,
    wind_load=4,
    wind_overload=2.2,
    tension_overload=1.3,
    ice_thickness=0.5,
    wind_angle=dct.northwind,
    deflection_factor=1)

pcc=poleCalculationClass(config)
pcc.run(plot_format='pdf')

fcc=pcd.faultCalculationClass()
fcc.calcImpedanceLaunch(projectdir,projectname,60,3)
print(fcc.xfmr(150,8,False,'rand',1))
