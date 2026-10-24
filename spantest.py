# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 09:46:06 2019

@author: user
"""
from pc_classes import polecad as pc
from pc_classes.pc_functions import dataconstants as dct


projectname='Spans'
projectdir='./PoleCadTests/'+projectname+'/'

designTension=0.5
strengthFactor=0.65
windLoad=4
windOverload=2.5
tensionOverload=1.65
iceThickness=0.5
windAngle=dct.eastwind
deflectionFactor=1

pcc=pc.poleCalculationClass()
pcc.spanLaunch(projectname,projectdir,designTension,strengthFactor,windLoad,windOverload,tensionOverload,iceThickness,windAngle,deflectionFactor)


#Strength Factors
#                                          B          C
#Ice & Wind (250B)                        0.65       0.85
#Extreme Wind (250C)                      1.0        1.0
#Extreme Ice with Concurrent Wind (250D)  0.75       0.75
