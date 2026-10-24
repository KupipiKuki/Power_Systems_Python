# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 09:46:06 2019

@author: user
"""
from pc_classes import powercad as pc
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

fcc=pc.faultCalculationClass()

projectname='vdrop'
projectdir='./vdrop/'

zt=np.array([(.1/1000)*500,(.0279/1000)*500])

vdrop=fcc.calcVoltageDrop(zt,240,40,0.95,2)
print(vdrop)
