# -*- coding: utf-8 -*-
"""
Created on Tue Apr 25 14:44:11 2023

@author: jmc53
"""

from pc_classes import powercad as pc
import numpy as np

sb=100.0e6
vb=np.array([115e3,
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

zxfmr=fcc.xfmr(20,8,False,False,0.9)*100/20

ifc=fcc.ifault(zxfmr,vf,0,0,0)
ifcD=fcc.ifault(zxfmr,vf,0,0,1)
print('Transformer fault at low side with infinite high side bus')
print('low side 3PH current',abs(ifc[9]*ib[1]))
print('high side 3PH current',abs(ifcD[9]*ib[0]))
print('low side SLG current',abs(ifc[0]*ib[1]))
print('high side LL current',abs(ifcD[3]*ib[0]))
print('')
ztlpu=np.array([[0.002904+0.033616j],
             [0.006421+0.051757j]])
ztlo=np.array([[4.462265+85.062653j],
             [6.897365+82.927933j]])
ztlpu1=np.array([[4.462265+85.062653j],
             [6.897365+82.927933j]])/(300e6/(vb[0]*np.sqrt(3)))
ztl=ztlpu
ifc=fcc.ifault(ztl,vf,0,0,0)
print('Transmission fault at high side bus')
print('Transmission 3PH current',abs(ifc[9]*ib[0]))
print('Transmission SLG current',abs(ifc[0]*ib[0]))
print('')
zt=ztl+zxfmr
ifc=fcc.ifault(zt,vf,0,0,0)
ifcD=fcc.ifault(zxfmr,vf,0,0,1)
print('Transformer fault at low side bus with transmission')
print('low side 3PH current',abs(ifc[9]*ib[1]))
print('high side 3PH current',abs(ifcD[9]*ib[0]))
print('low side SLG current',abs(ifc[0]*ib[1]))
print('high side LL current',abs(ifcD[3]*ib[0]))