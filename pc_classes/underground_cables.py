# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 11:15:31 2025

@author: jmc53
"""

import numpy as np
from cmath import rect
#(wet,swampy,average,dry/Rock,Rock/Concrete)
De_vals=[27.9,882,2790,8820,882e3,882e4]

#Nohm is the resistance of a single strand, ohm/mi
cables = {'4/0AWG':{'e_r' : 2.3,
                    'D_cond' : 0.504,
                    'D_strand' : 0.0641,
                    'k' : 11,
                    'R' : 1.334*0.5/12,
                    'DCohm' : 0.084*5.28,
                    'ACohm' : 0.11*5.28,
                    'Nohm' : 13.36},
          '500MCM':{'e_r' : 2.3,
                    'D_cond' : 0.772,
                    'D_strand' : 0.0808,
                    'k' : 16,
                    'R' : 1.602*0.5/12,
                    'DCohm' : 0.035*5.28,
                    'ACohm' : 0.047*5.28,
                    'Nohm' : 21.2256},
          '750MCM' :{'e_r' : 2.3,
                     'D_cond' : 0.949,
                     'D_strand' : 0.0641,
                     'k' : 19,
                     'R' : 1.823*0.5/12,
                     'DCohm' : 0.024*5.28,
                     'ACohm' : 0.032*5.28,
                     'Nohm' : 13.36},
          '1000MCM':{'e_r' : 2.3,
                     'D_cond' : 1.904,
                     'D_strand' : 0.0808,
                     'k' : 16,
                     'R' : 1.968*0.5/12,
                     'DCohm' : 0.018*5.28,
                     'ACohm' : 0.024*5.28,
                     'Nohm' : 21.2256}}

#Southwire custom neutral using spec 81241
tre_cables = {'4/0AWG':{'e_r' : 2.3,
                        'D_cond' : 0.498,
                        'D_strand' : 0.0808/2,
                        'k' : 14, # 14 strands of 12AWG (1/2)
                        'R' : (1.325+(1.553-0.05-1.325)/2)*0.5/12,
                        'DCohm' : 0.0836*5.28,
                        'ACohm' : 0.105*5.28,
                        'Nohm' : 1.65*5.28},
              '500MCM':{'e_r' : 2.3,
                        'D_cond' : 0.789,
                        'D_strand' : 0.0808/2,
                        'k' : 16,# 16 strands of 12AWG (1/3)
                        'R' : (1.625+(1.945-0.08-1.625)/2)*0.5/12,
                        'DCohm' : 0.0354*5.28,
                        'ACohm' : 0.045*5.28,
                        'Nohm' : 1.65*5.28},
              '750MCM' :{'e_r' : 2.3,
                         'D_cond' : 0.968,
                         'D_strand' : 0.0808/2,
                         'k' : 12,# 12 strands of 12AWG (1/6)
                         'R' : (1.843+(2.163-0.08-1.843)/2)*0.5/12,
                         'DCohm' : 0.0236*5.28,
                         'ACohm' : 0.03*5.28,
                         'Nohm' : 1.65*5.28},
              '1000MCM':{'e_r' : 2.3,
                         'D_cond' : 1.117,
                         'D_strand' : 0.0808/2,
                         'k' : 16,# 16 strands of 12AWG (1/6)
                         'R' : (1.992+(2.356-0.08-1.992)/2)*0.5/12,
                         'DCohm' : 0.0177*5.28,
                         'ACohm' : 0.023*5.28,
                         'Nohm' : 1.65*5.28},
              '1250MCM':{'e_r' : 2.3,
                         'D_cond' : 1.250,
                         'D_strand' : 0.0808/2,
                         'k' : 16,# 16 strands of 12AWG (1/9)
                         'R' : (1.992+(2.356-0.08-1.992)/2)*0.5/12,
                         'DCohm' : 0.0141*5.28,
                         'ACohm' : 0.019*5.28,
                         'Nohm' : 1.65*5.28}}

class CableCapacitance:
    
    def __init__(self,
                 data=None):
        if isinstance(data,dict):
            try:
                self.e_r=data['e_r']
                self.R=data['R']
                self.k=data['k']
                self.Rdc=data['D_cond']/2
                self.Rds=data['D_strand']/2
            except:
                raise KeyError('Dictionary does not contain required keys')
        elif isinstance(data,list):
            try:
                self.Rdc=data[0]/2
                self.Rds=data[1]/2
                self.R=data[2]
                self.k=data[3]
                self.e_r=data[4]
            except:
                raise ValueError('Data list is wrong length')
        else:
            raise TypeError('Data must be a dictionary or list')
        self.Cpg=0
        self.Yag=0
        #e_o=8.854e-12 F/m convert to F/mi
        self.e_o=8.854e-12*5280/(1000/25.4/12)
        
    def Calc_Capacitance(self):
        self.Cpg=(2*np.pi*self.e_o*self.e_r)/(np.log(self.R/self.Rdc)-(1/self.k)*np.log((self.k*self.Rds)/self.R))


    def Calc_Admittance(self):
        self.Yag=2*np.pi*60*self.Cpg*1j

class CableImpedance:
    
    def __init__(self,data=None,frequency=60,De=2790):
        
        if isinstance(data,dict):
            try:
                self.f=frequency
                self.w = 2.0224e-3
                self.resd = 1.588e-3*self.f
                self.k=data['k']
                self.R=data['R']
                self.GMRc=0.7788*data['D_cond']/2
                self.GMRcn=(data['D_strand']*self.k*self.R**(self.k-1))**(1/self.k)
                self.Cres=data['ACohm']
                self.CNres=data['Nohm']/self.k
            except:
                raise KeyError('Dictionary does not contain required keys')
        elif isinstance(data,list):
            try:
                self.f=frequency
                self.w = 2.0224e-3
                self.resd = 1.588e-3*self.f
                self.k=data[5]
                self.R=data[4]
                self.GMRc=0.7788*data[2]/2
                self.GMRcn=(data[3]*self.k*self.R**(self.k-1))**(1/self.k)
                self.Cres=data[0]
                self.CNres=data[1]/self.k
            except:
                raise ValueError('Data list is wrong length')
        else:
            raise TypeError('Data must be a dictionary or list')
        
        self.De=De
        self.Zp=0
        self.Zn=0
        self.Zabc=None
        self.Zseq=None
        self.Z1=None
        self.Z0=None

    def Calc_Impedance(self):
        self.Zp=self.Cres+self.resd+1j*self.w*self.f*np.log(self.De/self.GMRc)
        self.Zn=self.CNres+self.resd+1j*self.w*self.f*np.log(self.De/self.GMRcn)

    def Calc_Impedance_Matrix(self,Dabc=[0.5,0.5,1]):

        dmat=np.array([0,Dabc[0],Dabc[2],self.R*1j,Dabc[0]+(self.R*1j),Dabc[2]+(self.R*1j)])
        Zmat=np.empty((6,6), dtype=np.complex128)
            
        for i in range(6):
            for j in range(6):
                if i!=j:
                    Zmat[i,j]=self.resd+1j*self.w*self.f*np.log(self.De/(abs(dmat[i]-dmat[j])))
            if i<3:
                Zmat[i,i]=self.Zp
            else:
                Zmat[i,i]=self.Zn
        
        zabc=Zmat[0:3,0:3]-np.dot(np.dot(Zmat[0:3,3:6],np.linalg.inv(Zmat[3:6,3:6])),Zmat[0:3,3:6])
        
        a = rect(1,(2*np.pi)/3)
        A = np.array([[1, 1, 1], [1, a**2, a], [1, a, a**2]])
        
        zseq=np.linalg.inv(A)*zabc*A
        #Compute the zero sequence impedance
        self.Z0=zseq[0,0]+zseq[0,1]+zseq[0,2]
        #Compute the positive sequence impedance
        self.Z1=zseq[1,0]+zseq[1,1]+zseq[1,2]
        self.Zabc=zabc
        self.Zseq=zseq


# =============================================================================
# z40=CableImpedance(cables['4/0AWG'])
# z40.Calc_Impedance()
# z40.Calc_Impedance_Matrix()
# 
# test={
#      'D_cond' : 0.567,
#      'D_strand' : 0.00208,
#      'k' : 13,
#      'R' : 0.0511,
#      'ACohm' : 0.41,
#      'Nohm' : 14.8722}
# 
# ztest=CableImpedance(test)
# ztest.Calc_Impedance()
# ztest.Calc_Impedance_Matrix()
# =============================================================================
