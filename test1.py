# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 09:46:06 2019

@author: user
"""
import numpy as np
import polecad as pc
import powercad as pcd

#direction wind is blowing
northwind=(3*np.pi)/2
northwestwind=(7*np.pi)/4
westwind=0
southwestwind=(1*np.pi)/4
southwind=np.pi/2
southeastwind=(3*np.pi)/4
eastwind=np.pi
northeastwind=(5*np.pi)/4

projectname='Test1'
projectdir='./'+projectname+'/'

designTension=0.6
strengthFactor=0.85
windLoad=4
windOverload=2.2
tensionOverload=1.3
iceThickness=0.5
windAngle=northeastwind
deflectionFactor=1
overrideSpan=0
overrideAngle=1
pcc=pc.poleCalculationClass()
pcc.poleLaunch(projectname,projectdir,designTension,strengthFactor,windLoad,windOverload,tensionOverload,iceThickness,windAngle,deflectionFactor,overrideSpan,overrideAngle)
fcc=pcd.faultCalculationClass()
fcc.calcImpedanceLaunch(projectdir,projectname,60,3)
print(fcc.xfmr(150,8,False,'rand',1))