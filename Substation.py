# -*- coding: utf-8 -*-
#Impedance Line Calculator, three phase complete
#Written by: Jason Cheers
#
#LineImpedanceCalc.py

import os
import numpy as np
import functions.PScalcs as ps
import functions.curveload as cl
import functions.curveplot as cplotter
import functions.ifaultprint as ifp

def ss1(subname,vf,ib,zb,zf,zg,zt):
    
    circuitname='Circuit 1'
    
    datafile.write('\n')
    datafile.write(circuitname+' Fault Currents\n')
    
    recloser='Interstate'
    #Circuit 1 Interstate Breaker
    zl3=ps.calcimpedance('ACSR','Quail 2/0',7,1,'ACSR','Quail 2/0',4,25,50,60,'VC1.11',0.333,0.333,0.333)
    
    zlt=zt+zl3/zb[1]
    Iabc=ps.ifault(zlt,vf,zg,zf[0])*ib[1]
    datafile.write(recloser+' Recloser maximum fault\n')
    datafile.write('SLG Fault: %.2f' % abs(Iabc[0,0])+'A\n')
    datafile.write('3PH Fault: %.2f' % abs(Iabc[11,0])+'A\n')
    
    recloser='US Route'
    #Circuit 1 Highway Breaker
    zl4=ps.calcimpedance('ACSR','Quail 2/0',18,1,'ACSR','Quail 2/0',4,25,50,60,'VC1.11',0.333,0.333,0.333)
    #Circuit 1 End of Line Estimate
    zl5=ps.calcimpedance('ACSR','Swan 4',16,1,'ACSR','Swan 4',4,25,50,60,'VC1.11',0.333,0.333,0.333)
    
    zlt=zt+(zl3+zl4)/zb[1]
    Iabc=ps.ifault(zlt,vf,zg,zf[0])*ib[1]
    datafile.write(recloser+' Recloser maximum fault\n')
    datafile.write('SLG Fault: %.2f' % abs(Iabc[0,0])+'A\n')
    datafile.write('3PH Fault: %.2f' % abs(Iabc[11,0])+'A\n')
    
    datafile.write(circuitname+' end of line calculations\n')
    
    zlt=zt+(zl3+zl4+zl5)/zb[1]
    Iabc=ps.ifault(zlt,vf,zg,zf[0])*ib[1]
    ifaultmax=abs(Iabc[0,0])
    ifaultmaxname='Max SLG: '+'%.2f' % ifaultmax+'A'
    datafile.write('%s' % ifaultmaxname+'\n')
    ifp.iprint(Iabc)
    
    Iabc=ps.ifault(zlt,vf,zg,zf[1])*ib[1]
    ifaultmin=abs(Iabc[0,0])
    ifaultminname='Min SLG: '+'%.2f' % ifaultmin+'A'
    datafile.write('%s' % ifaultminname+'\n')
    ifp.iprint(Iabc)

    os.chdir('./functions')
    hs1fcurve=cl.curveload('R-105',280,1,1,1,0,0)
    hs1dcurve=cl.curveload('U4',280,1,2,1,0,0)
    hs1fgcurve=cl.curveload('8-113',140,1,1,1,0,0)
    hs1dgcurve=cl.curveload('3-140',140,1,1,1,0,0)
    us93dcurve=cl.curveload('U4',170,1,1.25,1,0,0)
    us93dgcurve=cl.curveload('U3',80,1,5,1,0,0)
    hbfcurve=cl.curveload('R-105',100,1,1,1,0,0)
    hbdcurve=cl.curveload('U4',100,1,0.75,1,0,0)
    hbfgcurve=cl.curveload('U3',60,1,0.5,1,0,0)
    hbdgcurve=cl.curveload('U3',60,1,2,1,0,0)
    hbOCBAcurve=cl.curveload('A_H',1,1,0,5,0,0)
    hbOCBBcurve=cl.curveload('B_H',1,1,0,5,0,0)
    os.chdir('..')

    filename='SS1-Phase Max'
    foldername='./Substation/'
    curvenames=['SS1 R-105 Fast','SS1 U4 Delayed','Interstate U4','US Route R-105 Fast','US Route U4 Delayed']
    
    cplotter.plot5curves(hs1fcurve,hs1dcurve,us93dcurve,hbfcurve,hbdcurve,curvenames,True,ifaultmax,ifaultmaxname,foldername,filename)
    filename='SS1-Phase Min'
    cplotter.plot5curves(hs1fcurve,hs1dcurve,us93dcurve,hbfcurve,hbdcurve,curvenames,True,ifaultmin,ifaultminname,foldername,filename)
    
    filename='SS1-Ground Max'
    curvenames=['SS1 8-113 Fast','SS1 3-140 Delayed','Interstate U3','US Route U3 Fast','US Route U3 Delayed']
    
    cplotter.plot5curves(hs1fgcurve,hs1dgcurve,us93dgcurve,hbfgcurve,hbdgcurve,curvenames,True,ifaultmax,ifaultmaxname,foldername,filename)
    filename='SS1-Ground Min'
    cplotter.plot5curves(hs1fgcurve,hs1dgcurve,us93dgcurve,hbfgcurve,hbdgcurve,curvenames,True,ifaultmin,ifaultminname,foldername,filename)
    
    filename='SS1-HACKBERRY'
    foldername='./Substation/'
    curvenames=['US Route R-105 Fast','US Route U4 Delayed','Type H A','Type H B']
    
    cplotter.plot4curves(hbfcurve,hbdcurve,hbOCBAcurve,hbOCBBcurve,curvenames,True,ifaultmax,ifaultmaxname,foldername,filename)

#Substation Name
subname='Substation'
#Fault Current Filename
filename='Substation'
#Directory Name
foldername='./Substation/'

#Open The Data File
datafile=open(foldername+filename+'.txt', 'w+')
datafile.write(subname+' Fault Currents\n')


sb=100.0e6
vb=np.array([69.0e3,
             24.9e3])
ib=np.array([sb/(vb[0]*np.sqrt(3)),
             sb/(vb[1]*np.sqrt(3))])
zb=np.array([vb[0]**2/sb,
             vb[1]**2/sb])
zf=np.array([0,
             40/zb[1]])
zg=0
vf=1.05
    
#Source
zt1=ps.xfmr(90,15,ps.xrcalc(90.0,'norm'),1)*100.0/90.0
#Transmission Lines
zl1=ps.calcimpedance('ACSR','Quail 2/0',26.6,1,'ACSR','Quail 2/0',4,25,50,60,'TP-69G',0.333,0.333,0.333)
zl2=ps.calcimpedance('ACSR','Penguin 4/0',19.2,1,'ACSR','Raven 1/0',4,25,50,60,'TP-69G',0.333,0.333,0.333)
#Substation
zt2=ps.xfmr(12,7.4,ps.xrcalc(12,'norm'),1)*100.0/12.0
#Total Impedance At Substation
zt=zt1+(zl1+zl2)/zb[0]+zt2
#Calculate Fault At Substation
Iabc=ps.ifault(zt,vf,zg,zf[0])*ib[1]

#Write Substation Fault Data
datafile.write('\n')
datafile.write(subname+' maximum fault\n')
datafile.write('SLG Fault: %.2f' % abs(Iabc[0,0])+'A\n')
datafile.write('3PH Fault: %.2f' % abs(Iabc[11,0])+'A\n')

ss1(subname,vf,ib,zb,zf,zg,zt)
datafile.close()