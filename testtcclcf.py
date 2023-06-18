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

projectname='tcclcfTest'
projectdir='./'+projectname+'/'

fcc=pc.faultCalculationClass()
#fcc.tccLaunch(projectdir,projectname,1,7000,'7000A Max Fault')
projectname='tcclcfTest2'
fcc.tccGenerator(projectdir,projectname,1,7000,'7000A Max Fault',0,1200,'1200A Min Fault',1,5000,'5000A Coord Fault')

zt=fcc.xfmr(2.5,5.75,False,False,1)
print(zt)
ifc=fcc.ifault(zt,vf,zg,10/zb[1],1)
print(abs(ifc[0]*ib[1]))