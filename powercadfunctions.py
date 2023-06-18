# -*- coding: utf-8 -*-
"""
Created on Sun Jun 18 13:16:13 2023

@author: jmc53
"""

import numpy as np

class curve_calc:
    
    def __init__(self,x,Ip,CT,TD,adder,lcf,hcf,Ceq,coeff):
        self.Ip=Ip
        self.CT=CT
        self.TD=TD
        self.adder=adder
        self.lcf=lcf
        self.hcf=hcf
        self.Ceq=Ceq
        self.coeff=coeff
        self.curve=self.__get_step(x)
        
    def __get_step(self,x):
        #Curve U1-5/C1-5
        if self.Ceq==0:
            return np.array([x*self.Ip*self.CT,(self.TD*(self.coeff[0]+(self.coeff[1]/(x**self.coeff[2]-self.coeff[3]))))+self.adder])
        #Curve ITE
        elif self.Ceq==1:
            return np.array([x*self.Ip*self.CT,((self.coeff[0]+(self.coeff[1]/(x-self.coeff[2])**self.coeff[3]))*(((self.coeff[4]*self.TD)-self.coeff[5])/self.coeff[6]))])
        #Curve MICRO51
        elif self.Ceq==2:
            return np.array([x*self.Ip*self.CT,((self.coeff[0]+(self.coeff[1]/(x-self.coeff[2])**self.coeff[3]))*(((self.coeff[4]*self.TD)-self.coeff[5])/self.coeff[6]))])
        #Curve MCO
        elif self.Ceq==3:
            return np.array([x*self.Ip*self.CT,((self.coeff[0]+(self.coeff[1]/(x-self.coeff[2])**self.coeff[3]))*(self.TD/self.coeff[6]))])
        #Curve DPU
        elif self.Ceq==4:
            return np.array([x*self.Ip*self.CT,(((self.coeff[1]/(x**self.coeff[2]-self.coeff[3]))+self.coeff[0])*(((self.coeff[4]*self.TD)-self.coeff[5])/self.coeff[6]))])
        #Curve VacuFuse
        elif self.Ceq==5:
            return np.array([x*self.coeff[0],((self.coeff[1]/(((x**self.coeff[4])-self.coeff[3]))+self.coeff[2])*self.TD)])

    def get_step(self,x,delay=0):
        if delay==0:
            self.curve=np.vstack((self.curve,self.__get_step(x)))
        else:
            self.curve=np.vstack((self.curve,np.array([x*self.Ip*self.CT,delay])))