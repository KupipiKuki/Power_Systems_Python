# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 09:46:06 2019

@author: user
"""

from pc_classes import polecad as pc
from pc_classes import powercad as pcd
from pc_classes.pc_functions import dataconstants as dct

projectname='Test1'
projectdir='./PoleCadTests/'+projectname+'/'

designTension=0.6
strengthFactor=0.85
windLoad=4
windOverload=2.2
tensionOverload=1.3
iceThickness=0.5
windAngle=dct.northwind#northeastwind
deflectionFactor=1
pcc=pc.poleCalculationClass()
pcc.poleLaunch(projectname,projectdir,designTension,strengthFactor,windLoad,windOverload,tensionOverload,iceThickness,windAngle,deflectionFactor)
fcc=pcd.faultCalculationClass()
fcc.calcImpedanceLaunch(projectdir,projectname,60,3)
print(fcc.xfmr(150,8,False,'rand',1))