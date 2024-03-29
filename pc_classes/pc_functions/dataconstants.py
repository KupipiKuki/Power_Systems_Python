# -*- coding: utf-8 -*-
"""
Created on Sun Jun 25 13:18:12 2023

@author: jmc53
"""

import numpy as np

#Distribution Transformer Data (From RUS data) format kVA,%Z,Z angle (rad),R,X)
distxfmr = np.array([[5,2.1,0.523598776,0.018186533,0.0105],
                          [10,1.6,0.523598776,0.013856406,0.008],
                          [15,1.6,0.698131701,0.012256711,0.010284602],
                          [25,1.6,0.785398163,0.011313708,0.011313708],
                          [37.5,1.6,0.785398163,0.011313708,0.011313708],
                          [50,1.6,0.916297857,0.009740183,0.012693653],
                          [75,1.6,0.916297857,0.009740183,0.012693653],
                          [100,1.6,1.047197551,0.008,0.013856406],
                          [150,1.7,1.047197551,0.0085,0.014722432],
                          [167,1.7,1.047197551,0.0085,0.014722432]])

#xr ratio curve from GE manual MW,XR)
xrcurve = np.array([[0.05,1],
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

northwind=(3*np.pi)/2
northwestwind=(7*np.pi)/4
westwind=0
southwestwind=(1*np.pi)/4
southwind=np.pi/2
southeastwind=(3*np.pi)/4
eastwind=np.pi
northeastwind=(5*np.pi)/4