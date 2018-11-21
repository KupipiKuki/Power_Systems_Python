# -*- coding: utf-8 -*-
"""
Created on Wed Aug 28 14:41:27 2013

@author: jcheers
"""

import scipy as sp
from cmath import rect
from cmath import polar
from math import pi
from math import sqrt
import numpy as np

a = rect(1,(2*pi)/3)

Amat = sp.mat([[1, 1, 1], [1, a**2, a], [1, a, a**2]])
Ainv = (1.0/3.0)*sp.mat([[1, 1, 1], [1, a, a**2], [1, a**2, a]])
compd=(1/sqrt(3))*sp.array([[0],[(1-a)],[(1-a**2)]])
compy=(1/sqrt(3))*sp.array([[0],[(1-a**2)],[(1-a)]])

#xr ratio curve from GE manual MW,XR)
xrcurve = sp.array([[0.05,1],
                    [0.06,1.3],
                    [0.07,1.5],
                    [0.08,1.7],
                    [0.09,1.85],
                    [0.1,2],
                    [0.15,2.4],
                    [0.2,2.7],
                    [0.25,2.9],
                    [0.3,3],
                    [0.35,3.1],
                    [0.4,3.2],
                    [0.45,3.5],
                    [0.4999,3.8],
                    [0.5,4],
                    [0.6,4.5],
                    [0.7,5],
                    [0.8,5.3],
                    [0.9,5.7],
                    [1,6],
                    [1.5,6.8],
                    [2,7.4],
                    [2.5,8],
                    [2.9999,8.4],
                    [3,10.5],
                    [3.5,10.8],
                    [4,11.3],
                    [4.5,11.5],
                    [5,12],
                    [6,12.7],
                    [7,13.5],
                    [8,14.1],
                    [9,15],
                    [10,15.8],
                    [15,19],
                    [20,21.8],
                    [25,24],
                    [30,25.5],
                    [35,27],
                    [40,28.2],
                    [45,29.5],
                    [50,30.5],
                    [60,32.7],
                    [100,38],
                    [150,43],
                    [200,46]])
#Apparent Power Base
sb=100.0e6
#Voltage Base
vb=np.array([69.0e3,
             24.9e3,
             12.47e3,
             480,
             208])
#Current Base
ib=np.array([sb/(vb[0]*np.sqrt(3)),
             sb/(vb[1]*np.sqrt(3)),
             sb/(vb[2]*np.sqrt(3)),
             sb/(vb[3]*np.sqrt(3)),
             sb/(vb[4]*np.sqrt(3))])
#Impedance base
zb=np.array([vb[0]**2/sb,
             vb[1]**2/sb,
             vb[2]**2/sb,
             vb[3]**2/sb,
             vb[4]**2/sb])
#Fault Impedance
zf=np.array([0,
         5/zb[1],
         15/zb[1],
         5/zb[2],
         15/zb[2]])
#Ground Impedance
zg=np.array([0,
             10/zb[1],
             40/zb[1],
             10/zb[2],
             40/zb[2]])
#Fault Voltage
vf=1.05