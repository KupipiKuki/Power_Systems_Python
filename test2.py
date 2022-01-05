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

projectname='Test2'
projectdir='./'+projectname+'/'

designTension=0.5
strengthFactor=0.85
windLoad=9
windOverload=1.75
tensionOverload=1.3
iceThickness=0.0
windAngle=(3*np.pi)/2
deflectionFactor=1.2

pcc=pc.poleCalculationClass()
pcc.poleLaunch(projectname,projectdir,designTension,strengthFactor,windLoad,windOverload,tensionOverload,iceThickness,windAngle,deflectionFactor)