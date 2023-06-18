# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 09:46:06 2019

@author: user
"""
import powercad as pc
import numpy as np

sb=100.0e6
vb=np.array([34.5e3,
             12.47e3])
ib=np.array([sb/(vb[0]*np.sqrt(3)),
             sb/(vb[1]*np.sqrt(3))])
zb=np.array([vb[0]**2/sb,
             vb[1]**2/sb])
zf=np.array([0,
             40/zb[1]])
zg=0
vf=1.05

#Shows how a pickup curve and a total clear curve can be created

projectname='tcctctest'
projectdir='./'+projectname+'/'

fcc=pc.faultCalculationClass()
fcc.tccGenerator(projectdir,projectname,1,6300,'6300A Max Fault',0,300,'300A Min Fault',1,2000,'2000A Coord Fault')
