# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 07:07:34 2019

(WinPython64-3740)

Python Version 3.7.4
Pandas Version 0.24.2
Numpy Version 1.16.4+mkl
Matplotlib Version 3.1.1

@author: jcheers
"""

import pandas as pd
import numpy as np
from cmath import rect
from cmath import polar
import re
from .pc_functions import testfunctions as tfn
from .pc_functions import datafunctions as dfn
from .pc_functions import dataconstants as dct
import scipy.stats as ssp

class faultCalculationClass():
    
    def __init__(self):
        
        self.wooddata = dfn.generate_pole_data()
        
        self.Acon=pd.read_csv('./pc_classes/pc_data/Construction/7200_A.csv')
        self.Bcon=pd.read_csv('./pc_classes/pc_data/Construction/7200_B.csv')
        self.Ccon=pd.read_csv('./pc_classes/pc_data/Construction/7200_C.csv')
        
        self.conductordb=dfn.generate_conductor_database()

        self.Amat,self.Ainv,self.compd,self.compy=dfn.generate_transforms()
        
        #Distribution Transformer Data (From RUS data) format kVA,%Z,Z angle (rad),R,X)
        self.distxfmr = dct.distxfmr
        
        #xr ratio curve from GE manual MW,XR)
        self.xrcurve = dct.xrcurve

    def calcCurrent(self):

    	#windval of 2 typically covers most bad conditions, could be turned into an argument to be changed
        windval=2
    	#most evaluations should be taken at the hottest point of the day, as that would produce the most stress, intensity of 96 provides a reasonable case
        sunintensity=96
    	#altitude of 90 would be directly above conductor
        sunaltitude=90
    	#azimuth only affects the conductor if the altitude is something other then 90 degrees
        sunazimuth=0
    	#conductor azimuth would only come into play if the altitude were something other then 90 and the sun azimuth may come into play as well
        condazimuth=0
    	#This is the altitude of the conductor above sea level
        altitude=1000
        
        try:
            self.conddb.columns.get_loc('TAmb')
        except KeyError:
            self.conddb=self.conddb.assign(TAmb=25)
        
        try:
            self.conddb.columns.get_loc('TRise')
        except KeyError:
            self.conddb=self.conddb.assign(TRise=50)
        
        try:
            self.conddb.columns.get_loc('GMR')
        except KeyError:
            self.conddb=self.conddb.assign(GMR=np.NaN)
        try:
            self.conddb.columns.get_loc('DCOhmsCalc')
        except KeyError:
            self.conddb=self.conddb.assign(DCOhmsCalc=np.NaN)
        try:
            self.conddb.columns.get_loc('ACOhmsCalc')
        except KeyError:
            self.conddb=self.conddb.assign(ACOhmsCalc=np.NaN)
        try:
            self.conddb.columns.get_loc('GMRCalc')
        except KeyError:
            self.conddb=self.conddb.assign(GMRCalc=np.NaN)
        try:
            self.conddb.columns.get_loc('OhmsCalc')
        except KeyError:
            self.conddb=self.conddb.assign(OhmsCalc=np.NaN)
        try:
            self.conddb.columns.get_loc('CurrentCalc')
        except KeyError:
            self.conddb=self.conddb.assign(CurrentCalc=np.NaN)
        
        for polenum in range(0, len(self.conddb.index)):
            pl1 = self.conductordb.loc[(self.conductordb.index.get_level_values(0)==self.conddb.iat[polenum,self.conddb.columns.get_loc('ConductorType')]) & (self.conductordb.name==self.conddb.iat[polenum,self.conddb.columns.get_loc('ConductorName')])]
            gmrval=pl1.iat[0,pl1.columns.get_loc('gmr')]
            dcohmval=pl1.iat[0,pl1.columns.get_loc('DCohms')]
            acohmval=pl1.iat[0,pl1.columns.get_loc('ACohms')]
            tempamb=self.conddb.iat[polenum,self.conddb.columns.get_loc('TAmb')]
            temprise=self.conddb.iat[polenum,self.conddb.columns.get_loc('TRise')]
            self.conddb.iat[polenum,self.conddb.columns.get_loc('GMR')]=gmrval
            self.conddb.iat[polenum,self.conddb.columns.get_loc('DCOhmsCalc')]=dcohmval
            self.conddb.iat[polenum,self.conddb.columns.get_loc('ACOhmsCalc')]=acohmval
            
            if self.conddb.iat[polenum,self.conddb.columns.get_loc('ConductorType')]=='Copper':
                conductortype=1
            elif self.conddb.iat[polenum,self.conddb.columns.get_loc('ConductorType')]=='ACCC':
                conductortype=2
            else:
                conductortype=3
        
        	#DC resistance per foot
            resdc=dcohmval/1000
        	#AC resistance per foot
            resac=acohmval/1000
            #radius in inches
            radius=gmrval*12
            #area of the wire in ft
            surfaceareaft=2*np.pi*gmrval
            #area of the wire for 12 inches
            surfaceareain=2*np.pi*radius*12
            #Temperature of the Conductor
            tempcond=temprise+tempamb
            #Temperature Ratio
            tf=(tempcond+tempamb)/2
            #air density at tf, lb/ft3
            pf=(0.080695-(0.000002901*altitude)+(0.000000000037*altitude**2))/(1+0.00367*tf)
            #absolute viscosity of air at tf, lb/h-ft
            uf=0.0415+0.00012034*tf-0.00000011442*tf**2+0.00000000019416*tf**3
            #thermal conductivity of air at tf, W/ft2/C
            kf=0.007388+0.0000227889*tf-0.00000000134328*tf**2
            #radiated heat loss, W/ft
            wr=0.138*radius*2*0.5*(((273+tempcond)/100.0)**4-((273+tempamb)/100.0)**4)
            #convected heat loss, W/ft
            if windval<=0:
                wc=0.283*np.sqrt(pf)*(radius*2)**0.75*(temprise)**1.25
            else:
                wc1=(1.01+0.371*((pf*windval*60*60*radius*2)/uf)**0.52)*kf*(temprise)
                wc2=(0.1695*((pf*windval*60*60*radius*2)/uf)**0.6)*kf*(temprise)
                wc=max(wc1,wc2)
            #Angle of the Sun in radians
            angle=(sunaltitude*np.pi/180)
            #Solar Heat Gain, W/ft
            ws=0.5*sunintensity*np.sin(np.arccos(np.cos(angle)*np.cos((sunazimuth*np.pi/180)-(condazimuth*np.pi/180))))*surfaceareaft
            #Maximum Solar Heat Gain, W/ft
            wsbase=0.5*100*np.sin(90*np.pi/180)*surfaceareaft
            #Losses in W/in2-ft
            powerloss=(wc+wr)/surfaceareain
            #Conductor Resistance Calculations
            if conductortype==2:
                resac=resdc+((resac-resdc)/(75-25))*(tempcond-25)
            elif conductortype==1:
                resdctemp=resdc*(1+0.00381*((75)-20))
                resacdc=resac/resdctemp
                resdc=resdc*(1+0.00381*(75-20))
                resac=resdc*resacdc
            else:
                resdctemp=resdc*(1+0.00403*(75-20))
                resacdc=resac/resdctemp
                resdc=resdc*(1+0.00403*((tempamb+temprise)-20))
                resac=resdc*resacdc
            ohmval=(resac*5280)
            #Calculates the base current before accounting for sun and wind
            currentbase=np.sqrt((37.7*radius*2*powerloss)/resac)
            if ws==0:
                current=currentbase
            else:
                if windval>0:
                    current=currentbase*(0.99-((0.05*radius*2)*(ws/wsbase)))
                else:
                    current=currentbase*(0.99-(0.07*(angle/(np.pi/2)))-((0.05*radius*2)*(ws/wsbase)))
    
            self.conddb.iat[polenum,self.conddb.columns.get_loc('GMRCalc')]=gmrval
            self.conddb.iat[polenum,self.conddb.columns.get_loc('OhmsCalc')]=ohmval
            self.conddb.iat[polenum,self.conddb.columns.get_loc('CurrentCalc')]=current
    
    def calcImpedance(self,environmenttype,f):
        
        self.towerCalc()
        
        try:
            self.poledb.columns.get_loc('Span')
        except KeyError:
            self.poledb=self.poledb.assign(Span=np.NaN)
        
        try:
            self.conddb.columns.get_loc('Span')
        except KeyError:
            self.conddb=self.conddb.assign(Span=np.NaN)
        
        for polenum in range(0, len(self.poledb.index)):
            if tfn.testPositiveFloat(self.poledb.iat[polenum,self.poledb.columns.get_loc('Span')])==False:
                if self.poledb.index.values[polenum][2] == 0:
                    refx=self.poledb.iat[polenum,self.poledb.columns.get_loc('MapX')]
                    refy=self.poledb.iat[polenum,self.poledb.columns.get_loc('MapY')]
                normx=self.poledb.iat[polenum,self.poledb.columns.get_loc('MapX')]-refx
                normy=self.poledb.iat[polenum,self.poledb.columns.get_loc('MapY')]-refy
                
                if self.poledb.index.values[polenum][2] > 0:
                    span=np.sqrt(normx*normx+normy*normy)
                    self.poledb.iat[polenum,self.poledb.columns.get_loc('Span')]=span
            #Adjust Span from feet to miles
            self.poledb.iat[polenum,self.poledb.columns.get_loc('Span')]=self.poledb.iat[polenum,self.poledb.columns.get_loc('Span')]/5280
        
        for polenum in range(0, len(self.conddb.index)):
            #Check to see if there is a valid entry in the Conductor Span, if not use the SPan data from the Pole List
            if tfn.testPositiveFloat(self.conddb.iat[polenum,self.conddb.columns.get_loc('Span')])==False:
                self.conddb.iat[polenum,self.conddb.columns.get_loc('Span')]=self.poledb.loc[(self.conddb.index[polenum][0],self.conddb.index[polenum][1]),'Span'].iat[0]
        
        self.conddb=self.conddb.assign(Z0real=np.NaN,Z0imag=np.NaN,Z1real=np.NaN,Z1imag=np.NaN)
        
        for polein in self.conddb.index:
            if polein[2]==0:
                pl1=self.conddb.loc[polein[0]]
                linetype=pl1.at[(polein[1],0),'LineType']
                w = 2.0224e-3
                resd = 1.588e-3*f
                #Soil Type (wet-1,swampy-2,average-3,dry-4)
                if environmenttype==1:
                    De=27.9
                elif environmenttype==2:
                    De=882
                elif environmenttype==3:
                    De=2790
                else:
                    De=8820
                #Check to see phase configuration (determined by tower)
                if linetype==3:
                    f1=0.33
                    f2=0.33
                    f3=0.33
                    fmat=np.mat([[f1,f2,f3],
                                 [f3,f1,f2],
                                 [f2,f3,f1]])
                    zsa=pl1.loc[(polein[1],0),'OhmsCalc']+resd+1j*w*f*np.log(De/pl1.loc[(polein[1],0),'GMRCalc'])
                    zsb=pl1.loc[(polein[1],1),'OhmsCalc']+resd+1j*w*f*np.log(De/pl1.loc[(polein[1],1),'GMRCalc'])
                    zsc=pl1.loc[(polein[1],2),'OhmsCalc']+resd+1j*w*f*np.log(De/pl1.loc[(polein[1],2),'GMRCalc'])
                    zk=resd+1j*w*f*np.mat([np.log(De/pl1.loc[(polein[1],0),'AB']),np.log(De/pl1.loc[(polein[1],0),'BC']),np.log(De/pl1.loc[(polein[1],0),'CA'])])*fmat
                    zabc=np.mat([[zsa, zk[0,0], zk[0,2]], [zk[0,0], zsb, zk[0,1]], [zk[0,2], zk[0,1], zsc]])
                    
    #                if neutral>1:
    #                    zsn=np.mat([[pl1.at[(polein[0],polein[1],3),pl1.columns.get_loc('OhmsCalc')]+resd+1j*w*f*np.log(De/pl1.at[(polein[0],polein[1],3),pl1.columns.get_loc('GMRCalc')]),resd+1j*w*f*np.log(De/self.conddb.iat[polenum,self.conddb.columns.get_loc('NN2')])],
    #                                [resd+1j*w*f*np.log(De/self.conddb.iat[polenum,self.conddb.columns.get_loc('NN2')]),pl1.at[(polein[0],polein[1],4),pl1.columns.get_loc('OhmsCalc')]+resd+1j*w*f*np.log(De/pl1.at[(polein[0],polein[1],4),pl1.columns.get_loc('GMRCalc')])]])
    #                    zkn=np.mat([[resd+1j*w*f*np.log(De/self.conddb.iat[polenum,self.conddb.columns.get_loc('AN')]),resd+1j*w*f*np.log(De/self.conddb.iat[polenum,self.conddb.columns.get_loc('BN')]),resd+1j*w*f*np.log(De/self.conddb.iat[polenum,self.conddb.columns.get_loc('CN')])],
    #                                [resd+1j*w*f*np.log(De/self.conddb.iat[polenum,self.conddb.columns.get_loc('AN2')]),resd+1j*w*f*np.log(De/self.conddb.iat[polenum,self.conddb.columns.get_loc('BN2')]),resd+1j*w*f*np.log(De/self.conddb.iat[polenum,self.conddb.columns.get_loc('CN2')])]])
    #                    zabc=zabc-zkn.T*zsn.I*zkn
    #                    
    #                else:
                    zsn=pl1.at[(polein[1],3),'OhmsCalc']+resd+1j*w*f*np.log(De/pl1.at[(polein[1],3),'GMRCalc'])
                    zkn=np.mat([resd+1j*w*f*np.log(De/pl1.at[(polein[1],0),'AN']),resd+1j*w*f*np.log(De/pl1.at[(polein[1],0),'BN']),resd+1j*w*f*np.log(De/pl1.at[(polein[1],0),'CN'])])
                    zabc=zabc-zkn.T*(1.0/zsn)*zkn
                    #print(zabc)
                elif linetype==2:
                    f1=.5
                    f2=.5
                    fmat=np.mat([[f1,f2,0],
                                  [f2,f1,0],
                                  [0,0,0]])
                    zsa=pl1.at[(polein[1],0),'OhmsCalc']+resd+1j*w*f*np.log(De/pl1.at[(polein[1],0),'GMRCalc'])
                    zsb=pl1.at[(polein[1],1),'OhmsCalc']+resd+1j*w*f*np.log(De/pl1.at[(polein[1],1),'GMRCalc'])
                    
                    zk=resd+1j*w*f*np.log(De/pl1.at[(polein[1],0),'AB'])*fmat
                    
                    zabc=np.mat([[zsa,zk[0,0],0],[zk[0,0],zsb,0],[0,0,0]])
    
                    zsn=pl1.at[(polein[1],2),'OhmsCalc']+resd+1j*w*f*np.log(De/pl1.at[(polein[1],2),'GMRCalc'])
                    zkn=np.mat([resd+1j*w*f*np.log(De/pl1.at[(polein[1],0),'AN']),resd+1j*w*f*np.log(De/pl1.at[(polein[1],0),'BN']),0])
                    zabc=zabc-zkn.T*(1.0/zsn)*zkn
                else:
                    zsa=pl1.iat[0,pl1.columns.get_loc('OhmsCalc')]+resd+1j*w*f*np.log(De/pl1.iat[0,pl1.columns.get_loc('GMRCalc')])
                    zabc=np.mat([[zsa,0,0],[0,0,0],[0,0,0]])
    
                    zsn=pl1.iat[0,pl1.columns.get_loc('OhmsCalc')]+resd+1j*w*f*np.log(De/pl1.iat[0,pl1.columns.get_loc('GMRCalc')])
                    zkn=resd+1j*w*f*np.log(De/1)#pl1.iat[0,pl1.columns.get_loc('AN')])
                    zabc[0,0]=zsn-(zkn*zkn)/zsn
                #Multiple Zabc matrix by line length
                zabc = zabc*pl1.iat[0,pl1.columns.get_loc('Span')]
                #Perform the transformation on Zabc to obtain the sequence impedance matrix Z012
                z012 = self.Ainv*zabc*self.Amat
                #print(z012)
                #Compute the zero sequence impedance
                z0=z012[0,0]+z012[0,1]+z012[0,2]
                #Compute the positive sequence impedance
                z1=z012[1,0]+z012[1,1]+z012[1,2]
                #zmatrix=np.array([[z1.real,z1.imag],
                #                [z0.real,z0.imag]])
                self.conddb.at[polein,'Z1real']=z1.real
                self.conddb.at[polein,'Z1imag']=z1.imag
                self.conddb.at[polein,'Z0real']=z0.real
                self.conddb.at[polein,'Z0imag']=z0.imag
    
    def towerCalc(self):
        
        try:
            self.conddb.columns.get_loc('LineType')
        except KeyError:
            self.conddb=self.conddb.assign(LineType=np.NaN)
        try:
            self.conddb.columns.get_loc('AB')
        except KeyError:
            self.conddb=self.conddb.assign(AB=np.NaN)
        try:
            self.conddb.columns.get_loc('BC')
        except KeyError:
            self.conddb=self.conddb.assign(BC=np.NaN)
        try:
            self.conddb.columns.get_loc('CA')
        except KeyError:
            self.conddb=self.conddb.assign(CA=np.NaN)
        try:
            self.conddb.columns.get_loc('AN')
        except KeyError:
            self.conddb=self.conddb.assign(AN=np.NaN)
        try:
            self.conddb.columns.get_loc('BN')
        except KeyError:
            self.conddb=self.conddb.assign(BN=np.NaN)
        try:
            self.conddb.columns.get_loc('CN')
        except KeyError:
            self.conddb=self.conddb.assign(CN=np.NaN)
            
        for polenum in self.conddb.index:
            if polenum[2]==0:
                test=self.conddb.at[polenum,'Assembly']
                if pd.isna(test)==False:
                    if re.findall(r"(^A)",test):
                        asm=self.Acon.loc[self.Acon.Name == test]
                        if asm.empty==True:
                            asm=self.Acon[self.Acon.Name.str.contains(test, na=False)]
                            if asm.empty==True:
                                asm=self.Acon.loc[self.Acon.AltName == test]
                                if asm.empty==True:
                                    asm=self.Acon[self.Acon.AltName.str.contains(test, na=False)]
                        if asm.empty==False:
                            sqrtx=(asm.at[asm.index[0],'Phase1X']+asm.at[asm.index[0],'NeutralX'])*(asm.at[asm.index[0],'Phase1X']+asm.at[asm.index[0],'NeutralX'])
                            sqrty=(asm.at[asm.index[0],'Phase1Hin']+asm.at[asm.index[0],'NeutralHin'])*(asm.at[asm.index[0],'Phase1Hin']+asm.at[asm.index[0],'NeutralHin'])
                            self.conddb.at[polenum,'AN']=np.sqrt(sqrtx+sqrty)/12
                        self.conddb.at[polenum,'LineType']=1
                                
                    elif re.findall(r"(^B)",test):
                        asm=self.Bcon.loc[self.Bcon.Name == test]
                        if asm.empty==True:
                            asm=self.Bcon[self.Bcon.Name.str.contains(test, na=False)]
                            if asm.empty==True:
                                asm=self.Bcon.loc[self.Bcon.Name == test]
                                if asm.empty==True:
                                    asm=self.Bcon[self.Bcon.AltName.str.contains(test, na=False)]
                        if asm.empty==False:
                            sqrtx=(asm.at[asm.index[0],'Phase1X']+asm.at[asm.index[0],'Phase2X'])*(asm.at[asm.index[0],'Phase1X']+asm.at[asm.index[0],'Phase2X'])
                            sqrty=(asm.at[asm.index[0],'Phase1Hin']+asm.at[asm.index[0],'Phase2Hin'])*(asm.at[asm.index[0],'Phase1Hin']+asm.at[asm.index[0],'Phase2Hin'])
                            self.conddb.at[polenum,'AB']=np.sqrt(sqrtx+sqrty)/12
                            sqrtx=(asm.at[asm.index[0],'Phase1X']+asm.at[asm.index[0],'NeutralX'])*(asm.at[asm.index[0],'Phase1X']+asm.at[asm.index[0],'NeutralX'])
                            sqrty=(asm.at[asm.index[0],'Phase1Hin']+asm.at[asm.index[0],'NeutralHin'])*(asm.at[asm.index[0],'Phase1Hin']+asm.at[asm.index[0],'NeutralHin'])
                            self.conddb.at[polenum,'AN']=np.sqrt(sqrtx+sqrty)/12
                            sqrtx=(asm.at[asm.index[0],'Phase2X']+asm.at[asm.index[0],'NeutralX'])*(asm.at[asm.index[0],'Phase2X']+asm.at[asm.index[0],'NeutralX'])
                            sqrty=(asm.at[asm.index[0],'Phase2Hin']+asm.at[asm.index[0],'NeutralHin'])*(asm.at[asm.index[0],'Phase2Hin']+asm.at[asm.index[0],'NeutralHin'])
                            self.conddb.at[polenum,'BN']=np.sqrt(sqrtx+sqrty)/12
                        self.conddb.at[polenum,'LineType']=2
                    elif re.findall(r"(^C)",test):
                        asm=self.Ccon.loc[self.Ccon.Name == test]
                        if asm.empty==True:
                            asm=self.Ccon[self.Ccon.Name.str.contains(test, na=False)]
                            if asm.empty==True:
                                asm=self.Ccon.loc[self.Ccon.AltName == test]
                                if asm.empty==True:
                                    asm=self.Ccon[self.Ccon.AltName.str.contains(test, na=False)]
                        if asm.empty==False:
                            sqrtx=(asm.at[asm.index[0],'Phase1X']+asm.at[asm.index[0],'Phase2X'])*(asm.at[asm.index[0],'Phase1X']+asm.at[asm.index[0],'Phase2X'])
                            sqrty=(asm.at[asm.index[0],'Phase1Hin']+asm.at[asm.index[0],'Phase2Hin'])*(asm.at[asm.index[0],'Phase1Hin']+asm.at[asm.index[0],'Phase2Hin'])
                            self.conddb.at[polenum,'AB']=np.sqrt(sqrtx+sqrty)/12
                            sqrtx=(asm.at[asm.index[0],'Phase2X']+asm.at[asm.index[0],'Phase3X'])*(asm.at[asm.index[0],'Phase2X']+asm.at[asm.index[0],'Phase3X'])
                            sqrty=(asm.at[asm.index[0],'Phase2Hin']+asm.at[asm.index[0],'Phase3Hin'])*(asm.at[asm.index[0],'Phase2Hin']+asm.at[asm.index[0],'Phase3Hin'])
                            self.conddb.at[polenum,'BC']=np.sqrt(sqrtx+sqrty)/12
                            sqrtx=(asm.at[asm.index[0],'Phase3X']+asm.at[asm.index[0],'Phase1X'])*(asm.at[asm.index[0],'Phase3X']+asm.at[asm.index[0],'Phase1X'])
                            sqrty=(asm.at[asm.index[0],'Phase3Hin']+asm.at[asm.index[0],'Phase1Hin'])*(asm.at[asm.index[0],'Phase3Hin']+asm.at[asm.index[0],'Phase1Hin'])
                            self.conddb.at[polenum,'CA']=np.sqrt(sqrtx+sqrty)/12
                            sqrtx=(asm.at[asm.index[0],'Phase1X']+asm.at[asm.index[0],'NeutralX'])*(asm.at[asm.index[0],'Phase1X']+asm.at[asm.index[0],'NeutralX'])
                            sqrty=(asm.at[asm.index[0],'Phase1Hin']+asm.at[asm.index[0],'NeutralHin'])*(asm.at[asm.index[0],'Phase1Hin']+asm.at[asm.index[0],'NeutralHin'])
                            self.conddb.at[polenum,'AN']=np.sqrt(sqrtx+sqrty)/12
                            sqrtx=(asm.at[asm.index[0],'Phase2X']+asm.at[asm.index[0],'NeutralX'])*(asm.at[asm.index[0],'Phase2X']+asm.at[asm.index[0],'NeutralX'])
                            sqrty=(asm.at[asm.index[0],'Phase2Hin']+asm.at[asm.index[0],'NeutralHin'])*(asm.at[asm.index[0],'Phase2Hin']+asm.at[asm.index[0],'NeutralHin'])
                            self.conddb.at[polenum,'BN']=np.sqrt(sqrtx+sqrty)/12
                            sqrtx=(asm.at[asm.index[0],'Phase3X']+asm.at[asm.index[0],'NeutralX'])*(asm.at[asm.index[0],'Phase3X']+asm.at[asm.index[0],'NeutralX'])
                            sqrty=(asm.at[asm.index[0],'Phase3Hin']+asm.at[asm.index[0],'NeutralHin'])*(asm.at[asm.index[0],'Phase3Hin']+asm.at[asm.index[0],'NeutralHin'])
                            self.conddb.at[polenum,'CN']=np.sqrt(sqrtx+sqrty)/12
                        self.conddb.at[polenum,'LineType']=3
    
    def ifault(self,zlt,vf,zgnd,zfault,matreturn):
        """
        ifault\n
        \n
        zlt - impedance in pu, np.array complex format [[r1+x1j],[r0+x0j]]
        vf - voltage in pu, float
        zgnd - ground impedance in pu, float
        zfault - fault impedance in pu, float
        matreturn:
            0 Iabc matrix
            1 Iabc matrix dy viewed from D
            2 Iabc matrix yd viewed from Y
            3 I012 matrix dy viewed from D
            4 I012 matrix yd viewed from Y
            5 I012 matrix
        """
        zt=zlt[0,0]
        z0t=zlt[1,0]
        #*********************************************************************#
        #Phase to Ground Fault, (A-G)
        #*********************************************************************#
        #Generate Phase Current Matrix From Sequence Current Matrix
        I012=np.array([[(vf/(z0t+zt+zt+zfault+(3*zgnd)))],
                       [(vf/(z0t+zt+zt+zfault+(3*zgnd)))],
                       [(vf/(z0t+zt+zt+zfault+(3*zgnd)))]])
        Iabc=np.dot(self.Amat,I012)
        Iseq=I012
        #Generate Results Moving Backwards from a low Wye to High Delta
        I012d=np.multiply(self.compy,I012)
        IabcD=np.dot(self.Amat,I012d)
        IseqD=I012d
        #Generate Results Moving Backwards from a low Delta to High Wye
        I012y=np.multiply(self.compd,Iseq)
        IabcY=np.dot(self.Amat,I012y)
        IseqY=I012y
        #*********************************************************************#
        #Phase to Phase Fault, (BC)
        #*********************************************************************#
        #Generate Phase Current Matrix From Sequence Current Matrix
        I012=np.array([[0],
        			   [(vf/(zt+zt+(zfault)))],
        			   [-vf/(zt+zt+(zfault))]])
        Iabc=np.vstack((Iabc,np.dot(self.Amat,I012)))
        Iseq=np.vstack((Iseq,I012))
        #Generate Results Moving Backwards from a low Wye to High Delta
        I012d=np.multiply(self.compy,I012)
        IabcD=np.vstack((IabcD,np.dot(self.Amat,I012d)))
        IseqD=np.vstack((IseqD,I012d))
        #Generate Results Moving Backwards from a low Delta to High Wye
        I012y=np.multiply(self.compd,I012)
        IabcY=np.vstack((IabcY,np.dot(self.Amat,I012y)))
        IseqY=np.vstack((IseqY,I012y))
        #*********************************************************************#
        #Phase to Phase to Ground Fault, (BC-G)
        #*********************************************************************#
        #Calculate Positive Sequence Impedance Equation
        #I1=vf/((zt+zfault)+(((zt+zfault)*(z0t+(3*zgnd)))/(zt+z0t+(3*zgnd))))
        I1=vf/(zt+(zfault/2)+((zt+(zfault/2))*(z0t+(zfault/2)+(3*zgnd)))/(zt+z0t+zfault+(3*zgnd)))
        #Generate Phase Current Matrix From Sequence Current Matrix
        #I012=np.array([[(-I1*((zt+zfault)/(zt+z0t+zfault+(3*zgnd))))],
        #			   [I1],
        #			   [(-I1*((z0t+zfault+(3*zgnd))/(zt+z0t+(2*zfault)+(3*zgnd))))]])
        I012=np.array([[-I1*(z0t/(zt+z0t))],
        			   [I1],
        			   [-I1*(zt/(zt+z0t))]])
        Iabc=np.vstack((Iabc,np.dot(self.Amat,I012)))
        Iseq=np.vstack((Iseq,I012))
        #Generate Results Moving Backwards from a low Wye to High Delta
        I012d=np.multiply(self.compy,I012)
        IabcD=np.vstack((IabcD,np.dot(self.Amat,I012d)))
        IseqD=np.vstack((IseqD,I012d))
        #Generate Results Moving Backwards from a low Delta to High Wye
        I012y=np.multiply(self.compd,I012)
        IabcY=np.vstack((IabcY,np.dot(self.Amat,I012y)))
        IseqY=np.vstack((IseqY,I012y))
        #*********************************************************************#
        #Three Phase to Ground Fault
        #*********************************************************************#
        #Calculate Positive Sequence Impedance Equation
        I1=(vf/(zt+zfault+zgnd))
        I012=np.array([[0],[I1],[0]])
        Iabc=np.vstack((Iabc,np.dot(self.Amat,I012)))
        Iseq=np.vstack((Iseq,I012))
        #Generate Results Moving Backwards from a low Wye to High Delta
        I012d=np.multiply(self.compy,I012)
        IabcD=np.vstack((IabcD,np.dot(self.Amat,I012d)))
        IseqD=np.vstack((IseqD,I012d))
        #Generate Results Moving Backwards from a low Delta to High Wye
        I012y=np.multiply(self.compd,I012)
        IabcY=np.vstack((IabcY,np.dot(self.Amat,I012y)))
        IseqY=np.vstack((IseqY,I012y))
        
        if matreturn==1:
            return IabcD
        elif matreturn==2:
            return IabcY
        elif matreturn==3:
            return IseqD
        elif matreturn==4:
            return IseqY
        elif matreturn==5:
            return Iseq
        else:
            return Iabc

    #xfmr(Transformer Base MVA,
    #     Transformer Base KV,
    #     Nameplate Percent Impedance,
    #     X/R ratio,
    #     Z1/Z0 ratio)
    def xfmr(self,MVAbase, Zpercent, XRratio=False, results=False, zeromult=1):
        """
        xfmr\n
        \n
        MVAbase - Transformer Base MVA, float
        Zpercent - Percent Impedance, float
        XRratio - Default False (random) or float
        results - 'rand' or False for random, 'rlow' random low range, 'rhigh' random high range
        zeromult - multiplier for zero sequence, float
        """
        #test to see if XRratio is a positive value
        if tfn.testPositiveFloat(XRratio)==False:
            XRratio=self.xrcalc(MVAbase,results)
        #Calculate Positive Sequence Per Unit Impedance From Percent Impedance and X/R Ratio
        z1=(Zpercent/100)
        #Calculate Positive Sequence Resistance From Percent Impedance and X/R Ratio
        r1=z1/np.sqrt(1+XRratio**2);
        #Calculate Positive Sequence Reactance From Percent Impedance and X/R Ratio
        x1=1j*r1*XRratio
        #Calculate Zero Sequence Resistance
        r0=r1*zeromult
        #Calculate Zero Sequence Reactance
        x0=x1*zeromult
        #Returns impedance matrix:
        z1=r1+x1
        z0=r0+x0
        return np.array([[z1],[z0]])
    
    def xrcalc(self,MVAbase,results):
        if tfn.testIsString(results)==False:
            results='rand'
        
        if results=='low':
            if MVAbase>=12:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*(2-1.677)
            elif MVAbase>=2.5:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*(2-1.5)
            elif MVAbase>=0.5:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*(2-1.3)
            else:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])
        elif results=='high':
            if MVAbase>=12:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*1.677
            elif MVAbase>=2.5:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*1.5
            elif MVAbase>=0.5:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*1.3
            else:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])
        elif results=='rlow':
            if MVAbase>=12:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*(1-abs(1-ssp.norm.rvs(loc=1,scale=(0.677/3))))
            elif MVAbase>=2.5:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*(1-abs(1-ssp.norm.rvs(loc=1,scale=(0.5/3))))
            elif MVAbase>=0.5:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*(1-abs(1-ssp.norm.rvs(loc=1,scale=(0.3/3))))
            else:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])
        elif results=='rhigh':
            if MVAbase>=12:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*(1+abs(1-ssp.norm.rvs(loc=1,scale=(0.677/3))))
            elif MVAbase>=2.5:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*(1+abs(1-ssp.norm.rvs(loc=1,scale=(0.5/3))))
            elif MVAbase>=0.5:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*(1+abs(1-ssp.norm.rvs(loc=1,scale=(0.3/3))))
            else:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])
        elif results=='rand':
            if MVAbase>=12:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*ssp.norm.rvs(loc=1,scale=(0.677/3))
            elif MVAbase>=2.5:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*ssp.norm.rvs(loc=1,scale=(0.5/3))
            elif MVAbase>=0.5:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])*ssp.norm.rvs(loc=1,scale=(0.3/3))
            else:
                XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])
        else:
            XRratio=np.interp(MVAbase,self.xrcurve[:,0],self.xrcurve[:,1])
        return XRratio
    
    def abcseq(self,abcmat):
        seqmat=self.Ainv*abcmat*self.Amat
        return seqmat
        
    def abc2seq(self,abc):
        seq=np.dot(self.Ainv,abc)
        return seq
        
    def seq2abc(self,seq):
        abc=np.dot(self.Amat,seq)
        return abc
    
    def dy1(self,ID):
        I012=np.dot(self.Ainv,ID)
        I012Y=np.multiply(self.compy,I012)
        IY=np.dot(self.Amat,I012Y)   
        return IY
    
    def yd1(self,IY):
        I012=np.dot(self.Ainv,IY)
        I012D=np.multiply(self.compd,I012)
        ID=np.dot(self.Amat,I012D)
        return ID
    
    #1=single phase, 2=Center Tapped Service 240/120, 3=Three Phase line to line drop
    def calcVoltageDrop(self,zt,vs,il,pf,phase):
        rf=np.sin(np.arccos(pf))
        vdrop=vs+il*zt[0]*pf+il*zt[1]*rf-np.sqrt(vs**2-(il*zt[1]*pf-il*zt[0]*rf)**2)
        if phase>2:
            return vdrop*np.sqrt(3)            
        elif phase>1:
            return vdrop*2
        else:
            return vdrop

    def calcImpedanceLaunch(self,projectdir,projectname,frequency,environmenttype):
        #self.prepData()
        self.poledb = pd.read_csv(projectdir+'poledb.csv',dtype={'StudyPoleTag' : str, 'PoleTag' : str})
        self.poledb = self.poledb.set_index(['StudyPoleTag','PoleTag','PoleNumber'])
        self.conddb = pd.read_csv(projectdir+'conddb.csv',dtype={'StudyPoleTag' : str, 'PoleTag' : str})
        self.conddb = self.conddb.set_index(['StudyPoleTag','PoleTag','PoleNumber'])
        self.calcCurrent()
        self.calcImpedance(environmenttype,frequency)
        self.conddb.to_csv(projectdir+'condfcc.csv')
        
    def calcVoltDropLaunch(self,projectdir,projectname,frequency,environmenttype):
        #self.prepData()
        self.poledb = pd.read_csv(projectdir+'poledb.csv',dtype={'StudyPoleTag' : str, 'PoleTag' : str})
        self.poledb = self.poledb.set_index(['StudyPoleTag','PoleTag','PoleNumber'])
        self.conddb = pd.read_csv(projectdir+'conddb.csv',dtype={'StudyPoleTag' : str, 'PoleTag' : str})
        self.conddb = self.conddb.set_index(['StudyPoleTag','PoleTag','PoleNumber'])
        self.calcCurrent()
        self.calcImpedance(environmenttype,frequency)