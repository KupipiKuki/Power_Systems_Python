# -*- coding: utf-8 -*-
#Impedance Line Calculator, three phase complete
#Written by: Jason Cheers
#
#LineImpedanceCalc.py

import PScalcs as ps

vf=1.05
zgnd=0
zfault=0

zt1=ps.xfmr(90,15,ps.xrcalc(90,'norm'),1)
zl1=ps.calcimpedance('ACSR','Quail 2/0',26.6,1,'ACSR','Quail 2/0',4,25,50,60,'TP-69G',0.333,0.333,0.333)
zl2=ps.calcimpedance('ACSR','Penguin 4/0',19.2,1,'ACSR','Raven 1/0',4,25,50,60,'TP-69G',0.333,0.333,0.333)
zt2=ps.xfmr(12,7.4,ps.xrcalc(12,'norm'),1)
zl3=ps.calcimpedance('ACSR','Swan 4',10,1,'ACSR','Swan 4',4,25,50,60,'VC1.11',0.333,0.333,0.333)
zl4=ps.calcimpedance('ACSR','Raven 1/0',3,1,'ACSR','Raven 1/0',4,25,50,60,'VA1.1',0,0,0)

zlt=(zt1+zt2+(zl1+zl2)/47.61)
Iabc=ps.ifault(zlt,vf,zgnd,zfault)*2318.68
print('Substation maximum fault SLG,3PH')
print((abs(Iabc[0,0])))
print((abs(Iabc[11,0])))

zlt=(zt1+zt2+(zl1+zl2)/47.61+(zl3)/6.2)
Iabc=ps.ifault(zlt,vf,zgnd,zfault)*2318.68
print('Recloser maximum fault SLG,3PH')
print((abs(Iabc[0,0])))
print((abs(Iabc[11,0])))

zlt=(zt1+zt2+(zl1+zl2)/47.61+(zl3+zl4)/6.2)
Iabc=ps.ifault(zlt,vf,zgnd,zfault)*2318.68
print('End of line maximum fault SLG')
print((abs(Iabc[0,0])))

zfault=40/6.2
Iabc=ps.ifault(zlt,vf,zgnd,zfault)*2318.68
print('End of line minimum fault SLG')
print((abs(Iabc[0,0])))
