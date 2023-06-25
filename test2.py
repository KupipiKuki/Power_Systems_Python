# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 09:46:06 2019

@author: user
"""
from pc_classes import polecad as pc
from pc_classes.pc_functions import dataconstants as dct

projectname='Test2'
projectdir='./PoleCadTests/'+projectname+'/'

designTension=0.5
strengthFactor=0.85
windLoad=9
windOverload=1.75
tensionOverload=1.3
iceThickness=0.0
windAngle=dct.northwind
deflectionFactor=1.2

pcc=pc.poleCalculationClass()
pcc.poleLaunch(projectname,projectdir,designTension,strengthFactor,windLoad,windOverload,tensionOverload,iceThickness,windAngle,deflectionFactor)