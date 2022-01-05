# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 09:46:06 2019

@author: user
"""
import numpy as np
import polecad as pc


#direction wind is blowing
northwind=(3*np.pi)/2
northwestwind=(7*np.pi)/4
westwind=0
southwestwind=(1*np.pi)/4
southwind=np.pi/2
southeastwind=(7*np.pi)/4
eastwind=np.pi
northeastwind=(5*np.pi)/4

projectname='Spans'
projectdir='./'+projectname+'/'

designTension=0.5
strengthFactor=0.65
windLoad=4
windOverload=2.5
tensionOverload=1.65
iceThickness=0.5
windAngle=eastwind
deflectionFactor=1

pcc=pc.poleCalculationClass()
pcc.spanLaunch(projectname,projectdir,designTension,strengthFactor,windLoad,windOverload,tensionOverload,iceThickness,windAngle,deflectionFactor)


#Strength Factors
#                                          B          C
#Ice & Wind (250B)                        0.65       0.85
#Extreme Wind (250C)                      1.0        1.0
#Extreme Ice with Concurrent Wind (250D)  0.75       0.75
