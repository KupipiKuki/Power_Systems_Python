# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 07:07:34 2019

(WinPython64-3740)

Python Version 3.9.5
Pandas Version 1.3.4
Numpy Version 1.21.0
Matplotlib Version 3.4.2

pd.show_versions(as_json=False)
print(numpy.__version__)
print(matplotlib.__version__)

@author: jcheers
"""

import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import testfunctions as tfn
import os
import warnings


class poleCalculationClass():
    
    def prepData(self):
    
        wd=pd.ExcelFile('./PoleData/WoodPoles.xlsx')
        
        for sh in range(0, len(wd.sheet_names)):
            shname=wd.sheet_names[sh]
            if sh==0:
                self.wooddata = pd.concat([wd.parse(shname)],keys=[shname],names=['Species','Number'])
            else:
                self.wooddata = pd.concat([self.wooddata,pd.concat([wd.parse(shname)],keys=[shname],names=['Species','Number'])])
        
        self.Acon=pd.read_csv('./Construction/7200_A.csv')
        self.Bcon=pd.read_csv('./Construction/7200_B.csv')
        self.Ccon=pd.read_csv('./Construction/7200_C.csv')
        acsr=pd.read_csv('./Conductors/ACSR.csv',encoding='ISO-8859-1')
        aaac=pd.read_csv('./Conductors/AAAC.csv')
        aac=pd.read_csv('./Conductors/AAC.csv')
        copper=pd.read_csv('./Conductors/COPPER.csv')
        copperweld=pd.read_csv('./Conductors/COPPERWELD40.csv')
        copperweldcopper=pd.read_csv('./Conductors/COPPERWELDCOPPER.csv')
        triplex=pd.read_csv('./Conductors/TRIPLEX.csv')
        self.conductordb=pd.concat([acsr,aaac,aac,copper,copperweld,copperweldcopper,triplex],keys=['ACSR','AAAC','AAC','Copper','Copperweld','CopperweldCopper','Triplex'])
    
        driliteOL=pd.read_csv('./Conductors/DRILITE.csv')
        drilite6m=pd.read_csv('./Conductors/DRILITE6M.csv')
        drilite10m=pd.read_csv('./Conductors/DRILITE10M.csv')
        drilite16m=pd.read_csv('./Conductors/DRILITE16M.csv')
        tel6m=pd.read_csv('./Conductors/TEL6M.csv')
        tel10m=pd.read_csv('./Conductors/TEL10M.csv')
        tel16m=pd.read_csv('./Conductors/TEL16M.csv')
        telOL=pd.read_csv('./Conductors/TELOL.csv')
        fortex6m=pd.read_csv('./Conductors/FORTEX6M.csv')
        fortex10m=pd.read_csv('./Conductors/FORTEX10M.csv')
        fortex16m=pd.read_csv('./Conductors/FORTEX16M.csv')
        self.cabledb=pd.concat([driliteOL,drilite6m,drilite10m,drilite16m,tel6m,tel10m,tel16m,telOL,fortex6m,fortex10m,fortex16m],keys=['Drilite','Drilite6M','Drilite10M','Drilite16M','Tel6M','Tel10M','Tel16M','Tel0L','Fortex6M','Fortex10M','Fortex16M'])
    
        #printProgressBar(polenum, totalpoles, prefix = 'Progress:', suffix = 'Complete', length = 50)
    def asmCalculator(self,projectdir):
    
        self.poledb = pd.read_csv(projectdir+'poledb.csv',dtype={'StudyPoleTag' : str, 'PoleTag' : str})
        self.poledb = self.poledb.set_index(['StudyPoleTag','PoleTag','PoleNumber'])
        self.conddb = pd.read_csv(projectdir+'conddb.csv',dtype={'StudyPoleTag' : str, 'PoleTag' : str})
        self.conddb = self.conddb.set_index(['StudyPoleTag','PoleTag','PoleNumber'])
        self.guydb = pd.read_csv(projectdir+'guydb.csv',dtype={'StudyPoleTag' : str, 'PoleTag' : str})
        self.guydb = self.guydb.set_index(['StudyPoleTag','PoleTag','PoleNumber'])
        
        try:
            self.commdb = pd.read_csv(projectdir+'commdb.csv',dtype={'StudyPoleTag' : str, 'PoleTag' : str})
            self.commdb = self.commdb.set_index(['StudyPoleTag','PoleTag','PoleNumber'])
        except:
            commdbnames=['Assembly','AssemblyHeight','ConductorType','ConductorName','DesignTension']
            commdbindex=pd.MultiIndex(levels=[[],[],[]],
                                      codes=[[],[],[]],
                                      names=[u'StudyPoleTag',u'PoleTag',u'PoleNumber'])
            self.commdb=pd.DataFrame(index=commdbindex, columns=commdbnames)
        
        try:
            self.cguydb = pd.read_csv(projectdir+'cguydb.csv',dtype={'StudyPoleTag' : str, 'PoleTag' : str})
            self.cguydb = self.cguydb.set_index(['StudyPoleTag','PoleTag','PoleNumber'])
        except:
            cguydbnames=['Assembly','GuyHeight','GuyType','GuyX','GuyY']
            cguydbindex=pd.MultiIndex(levels=[[],[],[]],
                                      codes=[[],[],[]],
                                      names=[u'StudyPoleTag',u'PoleTag',u'PoleNumber'])
            self.cguydb=pd.DataFrame(index=cguydbindex, columns=cguydbnames)
        
        #Add data columns to the pole database
        
        try:
            self.poledb.columns.get_loc('GradeHeight')
        except KeyError:
            self.poledb=self.poledb.assign(GradeHeight=np.NaN)
        
        try:
            self.conddb.columns.get_loc('Height')
        except KeyError:
            self.conddb=self.conddb.assign(Height=np.NaN)
        
        try:
            self.conddb.columns.get_loc('DesignTension')
        except KeyError:
            self.conddb=self.conddb.assign(DesignTension=np.NaN)
        
        try:
            self.conddb.columns.get_loc('Tension')
        except KeyError:
            self.conddb=self.conddb.assign(Tension=np.NaN)
        
        try:
            self.commdb.columns.get_loc('Height')
        except KeyError:
            self.commdb=self.commdb.assign(Height=np.NaN)
        
        try:
            self.commdb.columns.get_loc('DesignTension')
        except KeyError:
            self.commdb=self.commdb.assign(DesignTension=np.NaN)
            
        try:
            self.commdb.columns.get_loc('Tension')
        except KeyError:
            self.commdb=self.commdb.assign(Tension=np.NaN)
        
        
        #Calculate the angles of each line from the normal axis ('x'), This provides a common angular reference for all moment calculations and forces placed on the pole
        for polenum in range(0, len(self.poledb.index)):
            
            #Below calculates the pole height above grade, any errors or nan values
            #are entered as 16 feet, Pole Height as 20, and Class 7
        
            if pd.isna(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleHeight')]):
                self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleHeight')]=20
                self.poledb.iat[polenum,self.poledb.columns.get_loc('GradeHeight')]=16
        
            if pd.isna(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleClass')]):
                self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleClass')]=7
            
            if tfn.testPositiveFloat(self.poledb.iat[polenum,self.poledb.columns.get_loc('GradeHeight')]):
                pass
            else:
                ploc=self.wooddata.Height[self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleSpecies')]] == int(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleHeight')])
                self.poledb.iat[polenum,self.poledb.columns.get_loc('GradeHeight')]=int(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleHeight')])-self.wooddata.Depth[self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleSpecies')],ploc.loc[ploc].index[0]]       

        minheight=9999
        for polenum in range(0, len(self.conddb.index)):
            #Get Heights of conductor and guy atachments based on assembly, (Guy Heights temporarily added
            #here to make the guy claculations easier)
            #This section needs to be optimized
               
            if tfn.testPositiveFloat(self.conddb.iat[polenum,self.conddb.columns.get_loc('DesignTension')]):
                pass
            else:
                self.conddb.iat[polenum,self.conddb.columns.get_loc('DesignTension')]=self.designTension
            
            test=self.conddb.iat[polenum,self.conddb.columns.get_loc('Assembly')]
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
                        if tfn.testPositiveFloat(self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]):
                            pass
                        else:
                            if self.conddb.index[polenum][2]==0:
                                self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'Phase1Hin']/12+self.conddb.iat[polenum,self.conddb.columns.get_loc('AssemblyHeight')]
                            else:
                                self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'NeutralHin']/12+self.conddb.iat[polenum,self.conddb.columns.get_loc('AssemblyHeight')]
                                if minheight>self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]:
                                    minheight=self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]
                elif re.findall(r"(^B)",test):
                    asm=self.Bcon.loc[self.Bcon.Name == test]
                    if asm.empty==True:
                        asm=self.Bcon[self.Bcon.Name.str.contains(test, na=False)]
                        if asm.empty==True:
                            asm=self.Bcon.loc[self.Bcon.Name == test]
                            if asm.empty==True:
                                asm=self.Bcon[self.Bcon.AltName.str.contains(test, na=False)]
                    if asm.empty==False:
                        if tfn.testPositiveFloat(self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]):
                            pass
                        else:
                            if self.conddb.index[polenum][2]==0:
                                self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'Phase1Hin']/12+self.conddb.iat[polenum,self.conddb.columns.get_loc('AssemblyHeight')]
                            elif self.conddb.index[polenum][2]==1:
                                self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'Phase2Hin']/12+self.conddb.iat[polenum,self.conddb.columns.get_loc('AssemblyHeight')]
                            else:
                                self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'NeutralHin']/12+self.conddb.iat[polenum,self.conddb.columns.get_loc('AssemblyHeight')]
                                if minheight>self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]:
                                    minheight=self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]
                elif re.findall(r"(^C)",test):
                    asm=self.Ccon.loc[self.Ccon.Name == test]
                    if asm.empty==True:
                        asm=self.Ccon[self.Ccon.Name.str.contains(test, na=False)]
                        if asm.empty==True:
                            asm=self.Ccon.loc[self.Ccon.AltName == test]
                            if asm.empty==True:
                                asm=self.Ccon[self.Ccon.AltName.str.contains(test, na=False)]
                    if asm.empty==False:
                        if tfn.testPositiveFloat(self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]):
                            pass
                        else:
                            if self.conddb.index[polenum][2]==0:
                                self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'Phase1Hin']/12+self.conddb.iat[polenum,self.conddb.columns.get_loc('AssemblyHeight')]
                            elif self.conddb.index[polenum][2]==1:
                                self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'Phase2Hin']/12+self.conddb.iat[polenum,self.conddb.columns.get_loc('AssemblyHeight')]
                            elif self.conddb.index[polenum][2]==2:
                                self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'Phase3Hin']/12+self.conddb.iat[polenum,self.conddb.columns.get_loc('AssemblyHeight')]
                            else:
                                self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'NeutralHin']/12+self.conddb.iat[polenum,self.conddb.columns.get_loc('AssemblyHeight')]
                                if minheight>self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]:
                                    minheight=self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]
            if polenum==0:
                studypole=self.conddb.index[polenum][0]
            elif ((studypole!=self.conddb.index[polenum][0]) | (polenum==(len(self.conddb.index)-1))):
                self.poledb.at[(studypole,studypole,0),'NeutralHeight']=minheight
                studypole=self.conddb.index[polenum][0]
                minheight=9999
        
        #K and J assemblies default to a A3 for height at the moment if no Height entered.
        for polenum in range(0, len(self.conddb.index)):
            test=self.conddb.iat[polenum,self.conddb.columns.get_loc('Assembly')]
            if re.findall(r"(^J)",test):
                if tfn.testPositiveFloat(self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]):
                    pass
                else:
                    #self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'NeutralHeight']
                    asm=self.Acon.loc[self.Acon.Name == 'A1.1']
                    self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'NeutralHin']/12+self.conddb.iat[polenum,self.conddb.columns.get_loc('AssemblyHeight')]
                
            elif re.findall(r"(^K)",test):
                if tfn.testPositiveFloat(self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]):
                    pass
                else:
                    #self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'NeutralHeight']
                    asm=self.Acon.loc[self.Acon.Name == 'A1.1']
                    self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'NeutralHin']/12+self.conddb.iat[polenum,self.conddb.columns.get_loc('AssemblyHeight')]
            
        for polenum in range(0, len(self.guydb.index)):
            #Get Heights of conductor and guy atachments based on assembly, (Guy Heights temporarily added
            #here to make the guy claculations easier)
            #This section needs to be optimized
               
            if tfn.testPositiveFloat(self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]):
                pass
            elif tfn.testIsString(self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]):
                test=self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]
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
                            if self.guydb.index[polenum][2]==0:
                                self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.guydb.index[polenum][0],self.guydb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH1']/12
                            else:
                                if pd.isna(asm.at[asm.index[0],'GuyH2']):
                                    self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.guydb.index[polenum][0],self.guydb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH1']/12
                                else:
                                    self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.guydb.index[polenum][0],self.guydb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH2']/12
                    elif re.findall(r"(^B)",test):
                        asm=self.Bcon.loc[self.Bcon.Name == test]
                        if asm.empty==True:
                            asm=self.Bcon[self.Bcon.Name.str.contains(test, na=False)]
                            if asm.empty==True:
                                asm=self.Bcon.loc[self.Bcon.Name == test]
                                if asm.empty==True:
                                    asm=self.Bcon[self.Bcon.AltName.str.contains(test, na=False)]
                        if asm.empty==False:
                            if self.guydb.index[polenum][2]==0:
                                self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.guydb.index[polenum][0],self.guydb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH1']/12
                            elif self.guydb.index[polenum][2]==1:
                                if pd.isna(asm.at[asm.index[0],'GuyH2']):
                                    self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.guydb.index[polenum][0],self.guydb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH1']/12
                                else:
                                    self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.guydb.index[polenum][0],self.guydb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH2']/12
                            else:
                                if pd.isna(asm.at[asm.index[0],'GuyH3']):
                                    self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.guydb.index[polenum][0],self.guydb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH1']/12
                                else:
                                    self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.guydb.index[polenum][0],self.guydb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH3']/12
                    elif re.findall(r"(^C)",test):
                        asm=self.Ccon.loc[self.Ccon.Name == test]
                        if asm.empty==True:
                            asm=self.Ccon[self.Ccon.Name.str.contains(test, na=False)]
                            if asm.empty==True:
                                asm=self.Ccon.loc[self.Ccon.AltName == test]
                                if asm.empty==True:
                                    asm=self.Ccon[self.Ccon.AltName.str.contains(test, na=False)]
                        if asm.empty==False:
                            if self.guydb.index[polenum][2]==0:
                                self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.guydb.index[polenum][0],self.guydb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH1']/12
                            elif self.guydb.index[polenum][2]==1:
                                if pd.isna(asm.at[asm.index[0],'GuyH2']):
                                    self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.guydb.index[polenum][0],self.guydb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH1']/12
                                else:
                                    self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.guydb.index[polenum][0],self.guydb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH2']/12
                            elif self.guydb.index[polenum][2]==2:
                                if pd.isna(asm.at[asm.index[0],'GuyH3']):
                                    self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.guydb.index[polenum][0],self.guydb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH1']/12
                                else:
                                    self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.guydb.index[polenum][0],self.guydb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH3']/12
                            else:
                                if pd.isna(asm.at[asm.index[0],'GuyH3']):
                                    self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.guydb.index[polenum][0],self.guydb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH1']/12
                                else:
                                    self.guydb.iat[polenum,self.guydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'GuyH4']/12
        
        for polenum in range(0, len(self.commdb.index)):
            if tfn.testPositiveFloat(self.commdb.iat[polenum,self.commdb.columns.get_loc('DesignTension')]):
                pass
            else:
                self.commdb.iat[polenum,self.commdb.columns.get_loc('DesignTension')]=self.designTension
            
            if tfn.testPositiveFloat(self.commdb.iat[polenum,self.commdb.columns.get_loc('Height')]):
                pass
            elif tfn.testPositiveFloat(self.commdb.iat[polenum,self.commdb.columns.get_loc('AssemblyHeight')]):
                self.commdb.iat[polenum,self.commdb.columns.get_loc('Height')]=self.commdb.iat[polenum,self.commdb.columns.get_loc('AssemblyHeight')]
            else:
                if self.poledb.at[(self.commdb.index[polenum][0],self.commdb.index[polenum][0],0),'NeutralHeight']<9999:
                
                    if self.commdb.index[polenum][2]==0:
                        self.commdb.iat[polenum,self.commdb.columns.get_loc('Height')]=self.poledb.at[(self.commdb.index[polenum][0],self.commdb.index[polenum][0],0),'NeutralHeight']-4
                    elif self.commdb.index[polenum][2]==1:
                        self.commdb.iat[polenum,self.commdb.columns.get_loc('Height')]=self.poledb.at[(self.commdb.index[polenum][0],self.commdb.index[polenum][0],0),'NeutralHeight']-6
                    else:
                        self.commdb.iat[polenum,self.commdb.columns.get_loc('Height')]=self.poledb.at[(self.commdb.index[polenum][0],self.commdb.index[polenum][0],0),'NeutralHeight']-8
                else:
                    asm=self.Acon.loc[self.Acon.Name == 'A3']
                    self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]=self.poledb.at[(self.conddb.index[polenum][0],self.conddb.index[polenum][0],0),'GradeHeight']+asm.at[asm.index[0],'Phase1Hin']/12+self.conddb.iat[polenum,self.conddb.columns.get_loc('AssemblyHeight')]
            
        for polenum in range(0, len(self.cguydb.index)):
            #Get Heights of conductor and guy atachments based on assembly, (Guy Heights temporarily added
            #here to make the guy claculations easier)
            #This section needs to be optimized
               
            if tfn.testPositiveFloat(self.cguydb.iat[polenum,self.cguydb.columns.get_loc('GuyHeight')]):
                pass
            else:
                self.cguydb.iat[polenum,self.cguydb.columns.get_loc('GuyHeight')]=self.poledb.at[(self.cguydb.index[polenum][0],self.cguydb.index[polenum][0],0),'NeutralHeight']-4
        
        self.poledb.to_csv(projectdir+'poledb1.csv')
        self.conddb.to_csv(projectdir+'conddb1.csv')
        self.guydb.to_csv(projectdir+'guydb1.csv')
        
        self.poledb=self.poledb.assign(NormX=np.NaN,NormY=np.NaN,Span=np.NaN,NormAngle=np.NaN,
                             PoleCt=np.NaN,PoleCb=np.NaN,PoleCg=np.NaN,
                             Mrn=np.NaN,Mbn=np.NaN,Mr=np.NaN,Mb=np.NaN,
                             Mbx=np.NaN,Mby=np.NaN,
                             Mtx=np.NaN,Mty=np.NaN,Mgx=np.NaN,Mgy=np.NaN,
                             Mtcx=np.NaN,Mtcy=np.NaN,Mcgx=np.NaN,Mcgy=np.NaN,
                             Mcmax=np.NaN,Mcwsx=np.NaN,Mcwsy=np.NaN,
                             Mccwsx=np.NaN,Mccwsy=np.NaN,
                             Mex=np.NaN,Mey=np.NaN,
                             Mgndx=np.NaN,Mgndy=np.NaN,
                             Mcgndx=np.NaN,Mcgndy=np.NaN,
                             MtMapX=np.NaN,MtMapY=np.NaN,
                             MgMapX=np.NaN,MgMapY=np.NaN,
                             MgndMapX=np.NaN,MgndMapY=np.NaN,
                             McgndMapX=np.NaN,McgndMapY=np.NaN)
        
        self.conddb=self.conddb.assign(Mcn=np.NaN,Mc=np.NaN,
                             Mcmax=np.NaN,Mcmaxws=np.NaN,Mcmaxx=np.NaN,Mcmaxy=np.NaN,
                             Mcws=np.NaN,Mcwsx=np.NaN,Mcwsy=np.NaN,
                             Mtx=np.NaN,Mty=np.NaN)
        
        self.commdb=self.commdb.assign(Mcn=np.NaN,Mc=np.NaN,
                             Mcmax=np.NaN,Mcmaxws=np.NaN,Mcmaxx=np.NaN,Mcmaxy=np.NaN,
                             Mcws=np.NaN,Mcwsx=np.NaN,Mcwsy=np.NaN,
                             Mtx=np.NaN,Mty=np.NaN)
        
        try:
            self.conddb.columns.get_loc('Span')
        except KeyError:
            self.conddb=self.conddb.assign(Span=np.NaN)
            
        try:
            self.conddb.columns.get_loc('NormAngle')
        except KeyError:
            self.conddb=self.conddb.assign(NormAngle=np.NaN)
        
        try:
            self.commdb.columns.get_loc('Span')
        except KeyError:
            self.commdb=self.commdb.assign(Span=np.NaN)
            
        try:
            self.commdb.columns.get_loc('NormAngle')
        except KeyError:
            self.commdb=self.commdb.assign(NormAngle=np.NaN)
        
        self.guydb=self.guydb.assign(Mtx=np.NaN,Mty=np.NaN,GuyMapX=np.NaN,GuyMapY=np.NaN)
        
        try:
            self.guydb.columns.get_loc('GuyTension')
        except KeyError:
            self.guydb=self.guydb.assign(GuyTension=np.NaN)
        
        self.cguydb=self.cguydb.assign(Mtx=np.NaN,Mty=np.NaN,GuyMapX=np.NaN,GuyMapY=np.NaN)
        
        try:
            self.cguydb.columns.get_loc('GuyTension')
        except KeyError:
            self.cguydb=self.cguydb.assign(GuyTension=np.NaN)

    def poleCalculator(self):        
        #Calculate the angles of each line from the normal axis ('x'), This provides a common angular reference for all moment calculations and forces placed on the pole
        for polenum in range(0, len(self.poledb.index)):
            if self.poledb.index.values[polenum][2] == 0:
                refx=self.poledb.iat[polenum,self.poledb.columns.get_loc('MapX')]
                refy=self.poledb.iat[polenum,self.poledb.columns.get_loc('MapY')]
            normx=self.poledb.iat[polenum,self.poledb.columns.get_loc('MapX')]-refx
            normy=self.poledb.iat[polenum,self.poledb.columns.get_loc('MapY')]-refy
            
            self.poledb.iat[polenum,self.poledb.columns.get_loc('NormX')]=normx
            self.poledb.iat[polenum,self.poledb.columns.get_loc('NormY')]=normy
            if self.poledb.index.values[polenum][2] > 0:
                span=np.sqrt(normx*normx+normy*normy)
                
                normangle=np.arctan2(normy,normx)
                self.poledb.iat[polenum,self.poledb.columns.get_loc('Span')]=span
                self.poledb.iat[polenum,self.poledb.columns.get_loc('NormAngle')]=normangle
            
            #Below calculates the pole height above grade, any errors or nan values
            #are entered as 16 feet, Pole Height as 20, and Class 7
        
            if pd.isna(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleHeight')]):
                self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleHeight')]=20
                self.poledb.iat[polenum,self.poledb.columns.get_loc('GradeHeight')]=16
        
            if pd.isna(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleClass')]):
                self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleClass')]=7
            
            ploc=self.wooddata.Height[self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleSpecies')]] == int(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleHeight')])
            self.poledb.iat[polenum,self.poledb.columns.get_loc('GradeHeight')]=int(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleHeight')])-self.wooddata.Depth[self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleSpecies')],ploc.loc[ploc].index[0]]
            test=str(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleClass')])
            if re.findall(r"(^[H]d+)",test):
                pclass=re.findall(r"(^[H]d+)",test)
            else:
                pclass=int(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleClass')])
            #Fetch the Circumference of the Pole at the top
            self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleCt')]=self.wooddata.at[(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleSpecies')],0),pclass]
            #Fetch the Circumference of the Pole at the butt
            self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleCb')]=self.wooddata.at[(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleSpecies')],ploc.loc[ploc].index[0]),pclass]
            #Calculated the Circumference of the Pole at the ground
            self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleCg')]=(((self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleHeight')]-((self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleHeight')]*0.1)+2))*(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleCb')]-self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleCt')]))/(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleHeight')]-self.wooddata.at[(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleSpecies')],ploc.loc[ploc].index[0]),'Depth']))+self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleCt')]
            #Calculate the Resistance Moment of the Pole
            self.poledb.iat[polenum,self.poledb.columns.get_loc('Mrn')]=0.000264*8000*(self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleCg')]**3)
            #Calulate the Resistance Moment of the Pole including the NESC Strength Factor 
            self.poledb.iat[polenum,self.poledb.columns.get_loc('Mr')]=self.poledb.iat[polenum,self.poledb.columns.get_loc('Mrn')]*self.strengthFactor
            #Calculate the Wind and Ice Load on the Pole
            self.poledb.iat[polenum,self.poledb.columns.get_loc('Mbn')]=self.windLoad*(((2*self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleCt')])+self.poledb.iat[polenum,self.poledb.columns.get_loc('PoleCg')])/(72*np.pi))*(self.poledb.iat[polenum,self.poledb.columns.get_loc('GradeHeight')]*self.poledb.iat[polenum,self.poledb.columns.get_loc('GradeHeight')])
            #Calculate the Wind and Ice Load on the Pole including the NESC Wind Overload Factor
            self.poledb.iat[polenum,self.poledb.columns.get_loc('Mb')]=self.poledb.iat[polenum,self.poledb.columns.get_loc('Mbn')]*self.windOverload
            #Calculate the Wind and Ice Load on the Pole in the X Direction
            self.poledb.iat[polenum,self.poledb.columns.get_loc('Mbx')]=self.poledb.iat[polenum,self.poledb.columns.get_loc('Mb')]*np.cos((np.pi/2)-(((3*np.pi)/2)-self.windAngle))
            #Calculate the Wind and Ice Load on the Pole in the Y Direction
            self.poledb.iat[polenum,self.poledb.columns.get_loc('Mby')]=self.poledb.iat[polenum,self.poledb.columns.get_loc('Mb')]*np.sin((np.pi/2)-(((3*np.pi)/2)-self.windAngle))
    
    def conductorCalculator(self):
        for polenum in range(0, len(self.conddb.index)):
            pl1 = self.conductordb.loc[(self.conductordb.index.get_level_values(0)==self.conddb.iat[polenum,self.conddb.columns.get_loc('ConductorType')]) & (self.conductordb.name==self.conddb.iat[polenum,self.conddb.columns.get_loc('ConductorName')])]
            #Check to see if there is a valid entry in the Conductor Tension, if not use Design Tension from Conductor Data
            if tfn.testPositiveFloat(self.conddb.iat[polenum,self.conddb.columns.get_loc('Tension')])==False:
                self.conddb.iat[polenum,self.conddb.columns.get_loc('Tension')]=pl1.iat[0,pl1.columns.get_loc('strength')]*self.conddb.iat[polenum,self.conddb.columns.get_loc('DesignTension')]
            #Check to see if there is a valid entry in the Conductor Span, if not use the SPan data from the Pole List
            if tfn.testPositiveFloat(self.conddb.iat[polenum,self.conddb.columns.get_loc('Span')])==False | self.overrideSpan:
                self.conddb.iat[polenum,self.conddb.columns.get_loc('Span')]=self.poledb.loc[(self.conddb.index[polenum][0],self.conddb.index[polenum][1]),'Span'].iat[0]
            #Get the normal angle from the Pole List
            if tfn.testIsNumber(self.conddb.iat[polenum,self.conddb.columns.get_loc('NormAngle')])==False | self.overrideAngle:
                self.conddb.iat[polenum,self.conddb.columns.get_loc('NormAngle')]=self.poledb.loc[(self.conddb.index[polenum][0],self.conddb.index[polenum][1]),'NormAngle'].iat[0]
            #Calculate the Tension Moment in the X direction
            self.conddb.iat[polenum,self.conddb.columns.get_loc('Mtx')]=np.cos(self.conddb.iat[polenum,self.conddb.columns.get_loc('NormAngle')])*self.conddb.iat[polenum,self.conddb.columns.get_loc('Tension')]*self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]*self.tensionOverload
            #Calculate the Tension Moment in the Y direction
            self.conddb.iat[polenum,self.conddb.columns.get_loc('Mty')]=np.sin(self.conddb.iat[polenum,self.conddb.columns.get_loc('NormAngle')])*self.conddb.iat[polenum,self.conddb.columns.get_loc('Tension')]*self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]*self.tensionOverload
            #Calculate the Wind and Ice Load on the Conductor
            self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcn')]=((self.windLoad*(pl1.iat[0,pl1.columns.get_loc('diameter')]+(2*self.iceThickness)))/12)*self.conddb.iat[polenum,self.conddb.columns.get_loc('Height')]
            #Calculate the Wind and Ice Load on the Conductor including the NESC Wind Overload Factor
            self.conddb.iat[polenum,self.conddb.columns.get_loc('Mc')]=self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcn')]*self.windOverload*np.abs(np.cos(self.conddb.iat[polenum,self.conddb.columns.get_loc('NormAngle')]-(((3*np.pi)/2)-self.windAngle)))
            #Calculate the Wind and Ice Load on the Conductor at Transverse Maximum
            self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcmax')]=self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcn')]*self.windOverload
            #Calculate the Wind and Ice Load on the Conductor at Transverse Maximum including the Wind Span
            self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcmaxws')]=self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcmax')]*(self.conddb.iat[polenum,self.conddb.columns.get_loc('Span')]/2)
             #Calculate the Wind and Ice Load on the Conductor at Transverse Maximum in the X Direction
            self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcmaxx')]=self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcmaxws')]*np.cos(self.conddb.iat[polenum,self.conddb.columns.get_loc('NormAngle')]+(np.pi/2))
            #Calculate the Wind and Ice Load on the Conductor at Transverse Maximum in the Y Direction
            self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcmaxy')]=self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcmaxws')]*np.sin(self.conddb.iat[polenum,self.conddb.columns.get_loc('NormAngle')]+(np.pi/2))
            #Calculate the Wind and Ice Load on the Conductor including the Wind Span
            self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcws')]=self.conddb.iat[polenum,self.conddb.columns.get_loc('Mc')]*(self.conddb.iat[polenum,self.conddb.columns.get_loc('Span')]/2)
            #Calculate the Wind and Ice Load on the Conductor including the Wind Span in the X Direction
            self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcwsx')]=self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcws')]*np.cos((np.pi/2)-(((3*np.pi)/2)-self.windAngle))
            #Calculate the Wind and Ice Load on the Conductor including the Wind Span in the Y Direction
            self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcwsy')]=self.conddb.iat[polenum,self.conddb.columns.get_loc('Mcws')]*np.sin((np.pi/2)-(((3*np.pi)/2)-self.windAngle))
        
        
        self.condcalc=self.conddb
        #Remove the Study Poles from the conductor list
        for cdbin in self.conddb.index:
            if cdbin[0]==cdbin[1]:
                self.condcalc=self.condcalc.drop(index=cdbin)
    
    def commsCalculator(self):
        for polenum in range(0, len(self.commdb.index)):
            pl1 = self.cabledb.loc[(self.cabledb.index.get_level_values(0)==self.commdb.iat[polenum,self.commdb.columns.get_loc('ConductorType')]) & (self.cabledb.name==self.commdb.iat[polenum,self.commdb.columns.get_loc('ConductorName')])]
            #Check to see if there is a valid entry in the Conductor Tension, if not use Design Tension from Conductor Data
            if tfn.testPositiveFloat(self.commdb.iat[polenum,self.commdb.columns.get_loc('Tension')])==False:
                self.commdb.iat[polenum,self.commdb.columns.get_loc('Tension')]=pl1.iat[0,pl1.columns.get_loc('strength')]*self.commdb.iat[polenum,self.commdb.columns.get_loc('DesignTension')]
            #Check to see if there is a valid entry in the Conductor Span, if not use the SPan data from the Pole List
            if tfn.testPositiveFloat(self.commdb.iat[polenum,self.commdb.columns.get_loc('Span')])==False:
                self.commdb.iat[polenum,self.commdb.columns.get_loc('Span')]=self.poledb.at[(self.commdb.index[polenum][0],self.commdb.index[polenum][1]),'Span'][0]
            #Get the normal angle from the Pole List
            if tfn.testIsNumber(self.commdb.iat[polenum,self.commdb.columns.get_loc('NormAngle')])==False:
                self.commdb.iat[polenum,self.commdb.columns.get_loc('NormAngle')]=self.poledb.at[(self.commdb.index[polenum][0],self.commdb.index[polenum][1]),'NormAngle'][0]
            #Calculate the Tension Moment in the X direction
            self.commdb.iat[polenum,self.commdb.columns.get_loc('Mtx')]=np.cos(self.commdb.iat[polenum,self.commdb.columns.get_loc('NormAngle')])*self.commdb.iat[polenum,self.commdb.columns.get_loc('Tension')]*self.commdb.iat[polenum,self.commdb.columns.get_loc('Height')]*self.tensionOverload
            #Calculate the Tension Moment in the Y direction
            self.commdb.iat[polenum,self.commdb.columns.get_loc('Mty')]=np.sin(self.commdb.iat[polenum,self.commdb.columns.get_loc('NormAngle')])*self.commdb.iat[polenum,self.commdb.columns.get_loc('Tension')]*self.commdb.iat[polenum,self.commdb.columns.get_loc('Height')]*self.tensionOverload
            #Calculate the Wind and Ice Load on the Conductor
            self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcn')]=((self.windLoad*(pl1.iat[0,pl1.columns.get_loc('diameter')]+(2*self.iceThickness)))/12)*self.commdb.iat[polenum,self.commdb.columns.get_loc('Height')]
            #Calculate the Wind and Ice Load on the Conductor including the NESC Wind Overload Factor
            self.commdb.iat[polenum,self.commdb.columns.get_loc('Mc')]=self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcn')]*self.windOverload*np.abs(np.cos(self.commdb.iat[polenum,self.commdb.columns.get_loc('NormAngle')]-(((3*np.pi)/2)-self.windAngle)))
            #Calculate the Wind and Ice Load on the Conductor at Transverse Maximum
            self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcmax')]=self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcn')]*self.windOverload
            #Calculate the Wind and Ice Load on the Conductor at Transverse Maximum including the Wind Span
            self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcmaxws')]=self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcmax')]*(self.commdb.iat[polenum,self.commdb.columns.get_loc('Span')]/2)
            #Calculate the Wind and Ice Load on the Conductor at Transverse Maximum in the X Direction
            self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcmaxx')]=self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcmaxws')]*np.cos(self.commdb.iat[polenum,self.commdb.columns.get_loc('NormAngle')]+(np.pi/2))
            #Calculate the Wind and Ice Load on the Conductor at Transverse Maximum in the Y Direction
            self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcmaxy')]=self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcmaxws')]*np.sin(self.commdb.iat[polenum,self.commdb.columns.get_loc('NormAngle')]+(np.pi/2))
            #Calculate the Wind and Ice Load on the Conductor including the Wind Span
            self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcws')]=self.commdb.iat[polenum,self.commdb.columns.get_loc('Mc')]*(self.commdb.iat[polenum,self.commdb.columns.get_loc('Span')]/2)
            #Calculate the Wind and Ice Load on the Conductor including the Wind Span in the X Direction
            self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcwsx')]=self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcws')]*np.cos((np.pi/2)-(((3*np.pi)/2)-self.windAngle))
            #Calculate the Wind and Ice Load on the Conductor including the Wind Span in the Y Direction
            self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcwsy')]=self.commdb.iat[polenum,self.commdb.columns.get_loc('Mcws')]*np.sin((np.pi/2)-(((3*np.pi)/2)-self.windAngle))
        
        
        self.commcalc=self.commdb
        #Remove the Study Poles from the conductor list
        for cdbin in self.commdb.index:
            if cdbin[0]==cdbin[1]:
                self.commcalc=self.commcalc.drop(index=cdbin)
        
    def poleMoments(self):
        #Calculate the sum X and Y moment forces and remove the study pole from the list
        for cdbin in self.condcalc.index:
            pl1=self.condcalc.loc[cdbin[0]]
            self.poledb.loc[(cdbin[0],cdbin[0],0),'Mtx']=pl1['Mtx'].sum(skipna = True)
            self.poledb.loc[(cdbin[0],cdbin[0],0),'Mty']=pl1['Mty'].sum(skipna = True)
            self.poledb.loc[(cdbin[0],cdbin[0],0),'Mcmax']=pl1['Mcmax'].sum(skipna = True)
            self.poledb.loc[(cdbin[0],cdbin[0],0),'Mcwsx']=pl1['Mcwsx'].sum(skipna = True)
            self.poledb.loc[(cdbin[0],cdbin[0],0),'Mcwsy']=pl1['Mcwsy'].sum(skipna = True)
            
        for cdbin in self.commcalc.index:
            pl1=self.commcalc.loc[cdbin[0]]
            self.poledb.loc[(cdbin[0],cdbin[0],0),'Mtcx']=pl1['Mtx'].sum(skipna = True)
            self.poledb.loc[(cdbin[0],cdbin[0],0),'Mtcy']=pl1['Mty'].sum(skipna = True)
            self.poledb.loc[(cdbin[0],cdbin[0],0),'Mccwsx']=pl1['Mcwsx'].sum(skipna = True)
            self.poledb.loc[(cdbin[0],cdbin[0],0),'Mccwsy']=pl1['Mcwsy'].sum(skipna = True)
        
        
        #Create list of just the study poles
        self.polecalc=self.poledb.dropna(subset=['Mtx','Mty'])
        self.plcondlist=self.conddb.loc[pd.isna(self.conddb.Mtx)]
        
        #create a list of non-study poles
        self.poleNocalc=self.poledb.loc[pd.isna(self.poledb.Mtx)]
    
    def guyCalculator(self, isComms):
        #Calcute the forces on the guys if a defined angle is not given
        #To be reworked to be more dynamic allowing for known guy angles and unknown angles
        #which would then take the known calculation and apply it to the total moment, 
        #unknown locations would take the total moment and calculate best position 
        keyerr=False
        if isComms==False:
            guydb=self.guydb
        else:
            guydb=self.cguydb
        
        for polein in self.polecalc.index:
            #Test to see if a Guy exists on the Pole
            try:
                gl1=guydb.loc[(polein[0],polein[1])]
                keyerr=False
            except KeyError:
                keyerr=True
            #If a Guy exists then calculate guy tension and location
            if keyerr==False:
                for guynum in range(0,len(gl1.index)):
                    if tfn.testPositiveFloat(guydb.at[(polein[0],polein[1],guynum),'GuyHeight']):
                        if isComms==False:
                            #For Calculated Guys on a Study Pole divide the Tension by the number of Guys
                            guydb.at[(polein[0],polein[1],guynum),'Mtx']=(self.polecalc.at[polein,'Mtx']*(-1))/(len(gl1.index))
                            guydb.at[(polein[0],polein[1],guynum),'Mty']=(self.polecalc.at[polein,'Mty']*(-1))/(len(gl1.index))
                        else:
                            #For Calculated Guys on a Study Pole divide the Tension by the number of Guys
                            guydb.at[(polein[0],polein[1],guynum),'Mtx']=(self.polecalc.at[polein,'Mtcx']*(-1))/(len(gl1.index))
                            guydb.at[(polein[0],polein[1],guynum),'Mty']=(self.polecalc.at[polein,'Mtcy']*(-1))/(len(gl1.index))
                            
                        #Check to see if the Guy is Specified with known Guy Length and Normal Angle of Pole
                        if guydb.at[(polein[0],polein[1],guynum),'GuyType']==1:
                            #If the Tension, Length, and Normal Angle are specified calculate Guy Moment, else default to type 1:2 calculated
                            if tfn.testPositiveFloat(guydb.at[(polein[0],polein[1],guynum),'GuyTension']):
                                if tfn.testPositiveFloat(guydb.at[(polein[0],polein[1],guynum),'GuyX']):
                                    guydb.at[(polein[0],polein[1],guynum),'GuyType']=5
                                    print('Error on Guy Length at ' +str(polein)+ ' Defaulting to Type 5')
                                elif tfn.testAngleFloat(guydb.at[(polein[0],polein[1],guynum),'GuyY']):
                                    guydb.at[(polein[0],polein[1],guynum),'GuyType']=5
                                    print('Error on Guy Angle at ' +str(polein)+ ' Defaulting to Type 5')
                                else:
                                    guydb.at[(polein[0],polein[1],guynum),'Mtx']=guydb.at[(polein[0],polein[1],guynum),'GuyTension']*guydb.at[(polein[0],polein[1],guynum),'GuyHeight']*np.sin(np.arctan(guydb.at[(polein[0],polein[1],guynum),'GuyX']/guydb.at[(polein[0],polein[1],guynum),'GuyHeight']))*np.cos(guydb.at[(polein[0],polein[1],guynum),'GuyY'])
                                    guydb.at[(polein[0],polein[1],guynum),'Mty']=guydb.at[(polein[0],polein[1],guynum),'GuyTension']*guydb.at[(polein[0],polein[1],guynum),'GuyHeight']*np.sin(np.arctan(guydb.at[(polein[0],polein[1],guynum),'GuyX']/guydb.at[(polein[0],polein[1],guynum),'GuyHeight']))*np.sin(guydb.at[(polein[0],polein[1],guynum),'GuyY'])
                                    guydb.at[(polein[0],polein[1],guynum),'GuyMapX']=self.polecalc.at[polein,'MapX']+guydb.at[(polein[0],polein[1],guynum),'GuyX']
                                    guydb.at[(polein[0],polein[1],guynum),'GuyMapY']=self.polecalc.at[polein,'MapY']+guydb.at[(polein[0],polein[1],guynum),'GuyY']
                            else:
                                guydb.at[(polein[0],polein[1],guynum),'GuyType']=5
                                print('Error on Guy Tension at ' +str(polein)+ ' Defaulting to Type 5')
                        #Check to see if the Guy is Specified with known Guy X Position and Y Position
                        
                        if guydb.at[(polein[0],polein[1],guynum),'GuyType']==2:
                            #If the Tension, X Location, and Y Location are specified calculate Guy Moment, else default to type 1:2 calculated
                            if tfn.testPositiveFloat(guydb.at[(polein[0],polein[1],guynum),'GuyTension']):
                                if tfn.testIsNumber(guydb.at[(polein[0],polein[1],guynum),'GuyX']):
                                    guydb.at[(polein[0],polein[1],guynum),'GuyType']=5
                                    print('Error on Guy X Location at ' +str(polein)+ ' Defaulting to Type 5')
                                elif tfn.testIsNumber(guydb.at[(polein[0],polein[1],guynum),'GuyY']):
                                    guydb.at[(polein[0],polein[1],guynum),'GuyType']=5
                                    print('Error on Guy Y Location at ' +str(polein)+ ' Defaulting to Type 5')
                                #elif ((testIsZero(guydb.at[(polein[0],polein[1],guynum),'GuyX'])) & (testIsZero(guydb.at[(polein[0],polein[1],guynum),'GuyY']))):
                                    #guydb.at[(polein[0],polein[1],guynum),'GuyType']=5
                                    #print('Both Guy X and Y Location 0.0 ' +str(polein)+ ' Defaulting to Type 5')
                                else:
                                    guydb.at[(polein[0],polein[1],guynum),'Mtx']=guydb.at[(polein[0],polein[1],guynum),'GuyTension']*guydb.at[(polein[0],polein[1],guynum),'GuyHeight']*np.sin(np.arctan(np.sqrt((guydb.at[(polein[0],polein[1],guynum),'GuyX']*guydb.at[(polein[0],polein[1],guynum),'GuyX'])+(guydb.at[(polein[0],polein[1],guynum),'GuyY']*guydb.at[(polein[0],polein[1],guynum),'GuyY']))/guydb.at[(polein[0],polein[1],guynum),'GuyHeight']))*np.cos(np.arctan2(guydb.at[(polein[0],polein[1],guynum),'Guyy'],guydb.at[(polein[0],polein[1],guynum),'Guyx']))
                                    guydb.at[(polein[0],polein[1],guynum),'Mty']=guydb.at[(polein[0],polein[1],guynum),'GuyTension']*guydb.at[(polein[0],polein[1],guynum),'GuyHeight']*np.sin(np.arctan(np.sqrt((guydb.at[(polein[0],polein[1],guynum),'GuyX']*guydb.at[(polein[0],polein[1],guynum),'GuyX'])+(guydb.at[(polein[0],polein[1],guynum),'GuyY']*guydb.at[(polein[0],polein[1],guynum),'GuyY']))/guydb.at[(polein[0],polein[1],guynum),'GuyHeight']))*np.sin(np.arctan2(guydb.at[(polein[0],polein[1],guynum),'Guyy'],guydb.at[(polein[0],polein[1],guynum),'Guyx']))
                                    guydb.at[(polein[0],polein[1],guynum),'GuyMapX']=guydb.at[(polein[0],polein[1],guynum),'GuyX']
                                    guydb.at[(polein[0],polein[1],guynum),'GuyMapY']=guydb.at[(polein[0],polein[1],guynum),'GuyY']
                            else:
                                guydb.at[(polein[0],polein[1],guynum),'GuyType']=5
                                print('Error on Guy Tension at ' +str(polein)+ ' Defaulting to Type 5')
                        
                        #Check to see if the Guy is Overhead
                        if guydb.at[(polein[0],polein[1],guynum),'GuyType']==6:
                            if tfn.testIsNumber(guydb.at[(polein[0],polein[1],guynum),'GuyX']):
                                guydb.at[(polein[0],polein[1],guynum),'GuyType']=5
                                print('Error on Guy X Location at ' +str(polein)+ ' Defaulting to Type 5')
                            elif tfn.testIsNumber(guydb.at[(polein[0],polein[1],guynum),'GuyY']):
                                guydb.at[(polein[0],polein[1],guynum),'GuyType']=5
                                print('Error on Guy Y Location at ' +str(polein)+ ' Defaulting to Type 5')
                            elif tfn.testPositiveFloat(guydb.at[(polein[0],polein[1],guynum),'GuyTension']):    
                                guydb.at[(polein[0],polein[1],guynum),'Mtx']=guydb.at[(polein[0],polein[1],guynum),'GuyTension']*guydb.at[(polein[0],polein[1],guynum),'GuyHeight']*np.cos(np.arctan2(guydb.at[(polein[0],polein[1],guynum),'Guyy'],guydb.at[(polein[0],polein[1],guynum),'Guyx']))
                                guydb.at[(polein[0],polein[1],guynum),'Mty']=guydb.at[(polein[0],polein[1],guynum),'GuyTension']*guydb.at[(polein[0],polein[1],guynum),'GuyHeight']*np.sin(np.arctan2(guydb.at[(polein[0],polein[1],guynum),'Guyy'],guydb.at[(polein[0],polein[1],guynum),'Guyx']))
                                guydb.at[(polein[0],polein[1],guynum),'GuyMapX']=guydb.at[(polein[0],polein[1],guynum),'GuyX']
                                guydb.at[(polein[0],polein[1],guynum),'GuyMapY']=guydb.at[(polein[0],polein[1],guynum),'GuyY']
                            else:
                                guydb.at[(polein[0],polein[1],guynum),'GuyTension']=(np.sqrt((guydb.at[(polein[0],polein[1],guynum),'Mtx']*guydb.at[(polein[0],polein[1],guynum),'Mtx']+(guydb.at[(polein[0],polein[1],guynum),'Mty']*guydb.at[(polein[0],polein[1],guynum),'Mty'])))/guydb.at[(polein[0],polein[1],guynum),'GuyHeight'])
                        
                        #Check to see if the Guy is 1:1
                        if guydb.at[(polein[0],polein[1],guynum),'GuyType']==3:
                            guydb.at[(polein[0],polein[1],guynum),'GuyTension']=(np.sqrt((guydb.at[(polein[0],polein[1],guynum),'Mtx']*guydb.at[(polein[0],polein[1],guynum),'Mtx']+(guydb.at[(polein[0],polein[1],guynum),'Mty']*guydb.at[(polein[0],polein[1],guynum),'Mty'])))/guydb.at[(polein[0],polein[1],guynum),'GuyHeight'])/np.sin(np.arctan(1))
                            guydb.at[(polein[0],polein[1],guynum),'GuyX']=(guydb.at[(polein[0],polein[1],guynum),'GuyHeight'])*np.cos(np.arctan2(guydb.at[(polein[0],polein[1],guynum),'Mty'],guydb.at[(polein[0],polein[1],guynum),'Mtx']))
                            guydb.at[(polein[0],polein[1],guynum),'GuyMapX']=self.polecalc.at[polein,'MapX']+guydb.at[(polein[0],polein[1],guynum),'GuyX']
                            guydb.at[(polein[0],polein[1],guynum),'GuyY']=(guydb.at[(polein[0],polein[1],guynum),'GuyHeight'])*np.sin(np.arctan2(guydb.at[(polein[0],polein[1],guynum),'Mty'],guydb.at[(polein[0],polein[1],guynum),'Mtx']))
                            guydb.at[(polein[0],polein[1],guynum),'GuyMapY']=self.polecalc.at[polein,'MapY']+guydb.at[(polein[0],polein[1],guynum),'GuyY']
                        #Check to see if the Guy is 2:3
                        if guydb.at[(polein[0],polein[1],guynum),'GuyType']==4:
                            guydb.at[(polein[0],polein[1],guynum),'GuyTension']=(np.sqrt((guydb.at[(polein[0],polein[1],guynum),'Mtx']*guydb.at[(polein[0],polein[1],guynum),'Mtx']+(guydb.at[(polein[0],polein[1],guynum),'Mty']*guydb.at[(polein[0],polein[1],guynum),'Mty'])))/guydb.at[(polein[0],polein[1],guynum),'GuyHeight'])/np.sin(np.arctan(2/3))
                            guydb.at[(polein[0],polein[1],guynum),'GuyX']=(guydb.at[(polein[0],polein[1],guynum),'GuyHeight']*(2/3))*np.cos(np.arctan2(guydb.at[(polein[0],polein[1],guynum),'Mty'],guydb.at[(polein[0],polein[1],guynum),'Mtx']))
                            guydb.at[(polein[0],polein[1],guynum),'GuyMapX']=self.polecalc.at[polein,'MapX']+guydb.at[(polein[0],polein[1],guynum),'GuyX']
                            guydb.at[(polein[0],polein[1],guynum),'GuyY']=(guydb.at[(polein[0],polein[1],guynum),'GuyHeight']*(2/3))*np.sin(np.arctan2(guydb.at[(polein[0],polein[1],guynum),'Mty'],guydb.at[(polein[0],polein[1],guynum),'Mtx']))
                            guydb.at[(polein[0],polein[1],guynum),'GuyMapY']=self.polecalc.at[polein,'MapY']+guydb.at[(polein[0],polein[1],guynum),'GuyY']
                        #Check to see if the Guy is 1:2
                        if guydb.at[(polein[0],polein[1],guynum),'GuyType']==5:
                            guydb.at[(polein[0],polein[1],guynum),'GuyTension']=(np.sqrt((guydb.at[(polein[0],polein[1],guynum),'Mtx']*guydb.at[(polein[0],polein[1],guynum),'Mtx']+(guydb.at[(polein[0],polein[1],guynum),'Mty']*guydb.at[(polein[0],polein[1],guynum),'Mty'])))/guydb.at[(polein[0],polein[1],guynum),'GuyHeight'])/np.sin(np.arctan(1/2))
                            guydb.at[(polein[0],polein[1],guynum),'GuyX']=(guydb.at[(polein[0],polein[1],guynum),'GuyHeight']/2)*np.cos(np.arctan2(guydb.at[(polein[0],polein[1],guynum),'Mty'],guydb.at[(polein[0],polein[1],guynum),'Mtx']))
                            guydb.at[(polein[0],polein[1],guynum),'GuyMapX']=self.polecalc.at[polein,'MapX']+guydb.at[(polein[0],polein[1],guynum),'GuyX']
                            guydb.at[(polein[0],polein[1],guynum),'GuyY']=(guydb.at[(polein[0],polein[1],guynum),'GuyHeight']/2)*np.sin(np.arctan2(guydb.at[(polein[0],polein[1],guynum),'Mty'],guydb.at[(polein[0],polein[1],guynum),'Mtx']))
                            guydb.at[(polein[0],polein[1],guynum),'GuyMapY']=self.polecalc.at[polein,'MapY']+guydb.at[(polein[0],polein[1],guynum),'GuyY']
                            #IF anything else is in the Guy Type
                        else:
                            print('Guy Type missing, defaulting to type 5')
                            guydb.at[(polein[0],polein[1],guynum),'GuyTension']=(np.sqrt((guydb.at[(polein[0],polein[1],guynum),'Mtx']*guydb.at[(polein[0],polein[1],guynum),'Mtx']+(guydb.at[(polein[0],polein[1],guynum),'Mty']*guydb.at[(polein[0],polein[1],guynum),'Mty'])))/guydb.at[(polein[0],polein[1],guynum),'GuyHeight'])/np.sin(np.arctan(1/2))
                            guydb.at[(polein[0],polein[1],guynum),'GuyX']=(guydb.at[(polein[0],polein[1],guynum),'GuyHeight']/2)*np.cos(np.arctan2(guydb.at[(polein[0],polein[1],guynum),'Mty'],guydb.at[(polein[0],polein[1],guynum),'Mtx']))
                            guydb.at[(polein[0],polein[1],guynum),'GuyMapX']=self.polecalc.at[polein,'MapX']+guydb.at[(polein[0],polein[1],guynum),'GuyX']
                            guydb.at[(polein[0],polein[1],guynum),'GuyY']=(guydb.at[(polein[0],polein[1],guynum),'GuyHeight']/2)*np.sin(np.arctan2(guydb.at[(polein[0],polein[1],guynum),'Mty'],guydb.at[(polein[0],polein[1],guynum),'Mtx']))
                            guydb.at[(polein[0],polein[1],guynum),'GuyMapY']=self.polecalc.at[polein,'MapY']+guydb.at[(polein[0],polein[1],guynum),'GuyY']
                        if isComms==False:
                            if tfn.testIsNotNumber(self.polecalc.at[polein,'Mgx']):
                                self.polecalc.at[polein,'Mgx']=guydb.at[(polein[0],polein[1],guynum),'Mtx']
                            else:
                                self.polecalc.at[polein,'Mgx']=self.polecalc.at[polein,'Mgx']+guydb.at[(polein[0],polein[1],guynum),'Mtx']
                            if tfn.testIsNotNumber(self.polecalc.at[polein,'Mgy']):
                                self.polecalc.at[polein,'Mgy']=guydb.at[(polein[0],polein[1],guynum),'Mty']
                            else:
                                self.polecalc.at[polein,'Mgy']=self.polecalc.at[polein,'Mgy']+guydb.at[(polein[0],polein[1],guynum),'Mty']
                        else:
                            if tfn.testIsNotNumber(self.polecalc.at[polein,'Mcgx']):
                                self.polecalc.at[polein,'Mcgx']=guydb.at[(polein[0],polein[1],guynum),'Mtx']
                            else:
                                self.polecalc.at[polein,'Mcgx']=self.polecalc.at[polein,'Mgx']+guydb.at[(polein[0],polein[1],guynum),'Mtx']
                            if tfn.testIsNotNumber(self.polecalc.at[polein,'Mcgy']):
                                self.polecalc.at[polein,'Mcgy']=guydb.at[(polein[0],polein[1],guynum),'Mty']
                            else:
                                self.polecalc.at[polein,'Mcgy']=self.polecalc.at[polein,'Mgy']+guydb.at[(polein[0],polein[1],guynum),'Mty']
                    else:
                        print('GuyHeight value error' +str(polein))
        return guydb
                    
    #Moments displayed on the map are divided by 2000 simply for display purposes
    def totalMomentCalculator(self):
        for polein in self.polecalc.index:
            self.polecalc.at[polein,'MgMapX']=self.polecalc.at[polein,'MapX']+((self.polecalc.at[polein,'Mtx']+self.polecalc.at[polein,'Mgx'])/2000)
            self.polecalc.at[polein,'MgMapY']=self.polecalc.at[polein,'MapY']+((self.polecalc.at[polein,'Mty']+self.polecalc.at[polein,'Mgy'])/2000)
            self.polecalc.at[polein,'MtMapX']=self.polecalc.at[polein,'MapX']+((self.polecalc.at[polein,'Mtx'])/2000)
            self.polecalc.at[polein,'MtMapY']=self.polecalc.at[polein,'MapY']+((self.polecalc.at[polein,'Mty'])/2000)
            self.polecalc.at[polein,'Mgndx']=np.nansum([self.polecalc.at[polein,'Mbx'],self.polecalc.at[polein,'Mtx'],self.polecalc.at[polein,'Mcwsx'],self.polecalc.at[polein,'Mex']])
            self.polecalc.at[polein,'Mgndy']=np.nansum([self.polecalc.at[polein,'Mby'],self.polecalc.at[polein,'Mty'],self.polecalc.at[polein,'Mcwsy'],self.polecalc.at[polein,'Mey']])
            self.polecalc.at[polein,'Mcgndx']=np.nansum([self.polecalc.at[polein,'Mtcx'],self.polecalc.at[polein,'Mccwsx']])
            self.polecalc.at[polein,'Mcgndy']=np.nansum([self.polecalc.at[polein,'Mtcy'],self.polecalc.at[polein,'Mccwsy']])
            if (pd.isna(self.polecalc.at[polein,'Mgx']) | pd.isna(self.polecalc.at[polein,'Mgy'])):
                self.polecalc.at[polein,'MgndMapX']=self.polecalc.at[polein,'MapX']+((self.polecalc.at[polein,'Mgndx'])/2000)
                self.polecalc.at[polein,'MgndMapY']=self.polecalc.at[polein,'MapY']+((self.polecalc.at[polein,'Mgndy'])/2000)
            else:
                self.polecalc.at[polein,'MgndMapX']=self.polecalc.at[polein,'MapX']+((self.polecalc.at[polein,'Mgndx']+self.polecalc.at[polein,'Mgx'])/2000)
                self.polecalc.at[polein,'MgndMapY']=self.polecalc.at[polein,'MapY']+((self.polecalc.at[polein,'Mgndy']+self.polecalc.at[polein,'Mgy'])/2000)
            if (pd.isna(self.polecalc.at[polein,'Mcgx']) | pd.isna(self.polecalc.at[polein,'Mcgy'])):
                self.polecalc.at[polein,'McgndMapX']=self.polecalc.at[polein,'MapX']+((self.polecalc.at[polein,'Mcgndx'])/2000)
                self.polecalc.at[polein,'McgndMapY']=self.polecalc.at[polein,'MapY']+((self.polecalc.at[polein,'Mcgndy'])/2000)
            else:
                self.polecalc.at[polein,'McgndMapX']=self.polecalc.at[polein,'MapX']+((self.polecalc.at[polein,'Mcgndx']+self.polecalc.at[polein,'Mcgx'])/2000)
                self.polecalc.at[polein,'McgndMapY']=self.polecalc.at[polein,'MapY']+((self.polecalc.at[polein,'Mcgndy']+self.polecalc.at[polein,'Mcgy'])/2000)
    
    def polePlotter(self,rpformat):
        self.polesummary = pd.DataFrame(columns=['Pole Strength','Utility Moment','Utility Guyed Moment','Total Utility Moment','Communications Moment','Communications Guyed Moment','Total Communications Moment','Overall Pole Moment','Guy Required'])
            
        for polein in self.polecalc.index:
            resistMoment=self.polecalc.at[polein,'Mr']
            if (pd.isna(self.polecalc.at[polein,'Mgx']) | pd.isna(self.polecalc.at[polein,'Mgy'])):
                sqrtx=self.polecalc.at[polein,'Mgndx']*self.polecalc.at[polein,'Mgndx']
                sqrty=self.polecalc.at[polein,'Mgndy']*self.polecalc.at[polein,'Mgndy']
                gndMoment=np.sqrt(sqrtx+sqrty)*self.deflectionFactor
                bgndMoment=gndMoment
                guyMoment=0
            else:
                sqrtx=(self.polecalc.at[polein,'Mgndx']+self.polecalc.at[polein,'Mgx'])*(self.polecalc.at[polein,'Mgndx']+self.polecalc.at[polein,'Mgx'])
                sqrty=(self.polecalc.at[polein,'Mgndy']+self.polecalc.at[polein,'Mgy'])*(self.polecalc.at[polein,'Mgndy']+self.polecalc.at[polein,'Mgy'])
                gndMoment=np.sqrt(sqrtx+sqrty)*self.deflectionFactor
                sqrtx=self.polecalc.at[polein,'Mgndx']*self.polecalc.at[polein,'Mgndx']
                sqrty=self.polecalc.at[polein,'Mgndy']*self.polecalc.at[polein,'Mgndy']
                bgndMoment=np.sqrt(sqrtx+sqrty)
                sqrtx=self.polecalc.at[polein,'Mgx']*self.polecalc.at[polein,'Mgx']
                sqrty=self.polecalc.at[polein,'Mgy']*self.polecalc.at[polein,'Mgy']
                guyMoment=np.sqrt(sqrtx+sqrty)
            if (pd.isna(self.polecalc.at[polein,'Mcgx']) | pd.isna(self.polecalc.at[polein,'Mcgy'])):
                sqrtx=self.polecalc.at[polein,'Mcgndx']*self.polecalc.at[polein,'Mcgndx']
                sqrty=self.polecalc.at[polein,'Mcgndy']*self.polecalc.at[polein,'Mcgndy']
                cgndMoment=np.sqrt(sqrtx+sqrty)*self.deflectionFactor
                bcgndMoment=cgndMoment
                cguyMoment=0
            else:
                sqrtx=(self.polecalc.at[polein,'Mcgndx']+self.polecalc.at[polein,'Mcgx'])*(self.polecalc.at[polein,'Mcgndx']+self.polecalc.at[polein,'Mcgx'])
                sqrty=(self.polecalc.at[polein,'Mcgndy']+self.polecalc.at[polein,'Mcgy'])*(self.polecalc.at[polein,'Mcgndy']+self.polecalc.at[polein,'Mcgy'])
                cgndMoment=np.sqrt(sqrtx+sqrty)*self.deflectionFactor
                sqrtx=self.polecalc.at[polein,'Mcgndx']*self.polecalc.at[polein,'Mcgndx']
                sqrty=self.polecalc.at[polein,'Mcgndy']*self.polecalc.at[polein,'Mcgndy']
                bcgndMoment=np.sqrt(sqrtx+sqrty)
                sqrtx=self.polecalc.at[polein,'Mcgx']*self.polecalc.at[polein,'Mcgx']
                sqrty=self.polecalc.at[polein,'Mcgy']*self.polecalc.at[polein,'Mcgy']
                cguyMoment=np.sqrt(sqrtx+sqrty)
            arrowx=0.05*np.cos(self.windAngle+np.pi)
            arrowy=0.05*np.sin(self.windAngle+np.pi)
            if self.windAngle<np.pi:
                textx=0.7
                texty=0.315
            else:
                textx=0.7
                texty=0.285
            
            figwitdh=7
            figheight=9
            
            limmax=np.nanmax([self.poleNocalc.loc[(polein[0]),'Span']])
            xlim=np.ceil((limmax)/100);
            ylim=np.ceil(((figheight/figwitdh)*limmax)/100);
            xlimmin=self.polecalc.at[polein,'MapX']-xlim*100
            xlimmax=self.polecalc.at[polein,'MapX']+xlim*100
            ylimmin=self.polecalc.at[polein,'MapY']-ylim*100
            ylimmax=self.polecalc.at[polein,'MapY']+ylim*100
            fig = plt.figure(figsize=(figwitdh, figheight), dpi=80, facecolor='w', edgecolor='k')
            
            #fig.subplots_adjust(top=0.3) 
            ax=fig.add_subplot(111)#, aspect='equal', adjustable='box', anchor='C')
            self.polecalc.loc[polein[0]].plot(kind='scatter',x='MapX',y='MapY', color='g',ax=ax, marker='o',s=250, label='Study Pole')
            self.poleNocalc.loc[polein[0]].plot(kind='scatter',x='MapX',y='MapY',color='c',ax=ax, marker='o', label='Poles')
            self.polecalc.loc[polein[0]].plot(kind='scatter',x='MtMapX',y='MtMapY',color='r',ax=ax, marker='x',s=100, label='Conductor Tension Moment')
            self.polecalc.loc[polein[0]].plot(kind='scatter',x='McgndMapX',y='McgndMapY',color='m',ax=ax, marker='x',s=100, label='Communications Ground Moment')
            self.polecalc.loc[polein[0]].plot(kind='scatter',x='MgndMapX',y='MgndMapY',color='orange',ax=ax, marker='x',s=100, label='Ground Moment\nNot Including Communications')
            try:
                self.guydb.loc[polein[0]].plot(kind='scatter',x='GuyMapX',y='GuyMapY',color='k',ax=ax, marker='+',s=100, label='Guy Location')
            except KeyError:
                pass
            ax.set_xlim(xlimmin,xlimmax)
            ax.set_ylim(ylimmin,ylimmax)
            ax.arrow(0.7,0.3,arrowx,arrowy, head_width=0.01, head_length=0.01, transform=ax.transAxes, label='Wind')
            ax.text(textx,texty,'Wind', transform=ax.transAxes, horizontalalignment='center')
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles, labels, loc=0)
            ax.set_title(self.projectname+' Pole '+polein[0])
            ax.set_xlabel('Map X Coordinates')
            ax.set_ylabel('Map Y Coordinates')
            fig.text(0.1, 0.985, 'Resisting Moment: '+str(np.round(resistMoment,1)), fontsize=8)
            fig.text(0.1, 0.97, 'Ground Moment: '+str(np.round(gndMoment,1)), fontsize=8)
            fig.text(0.1, 0.955, 'Communications Ground Moment: '+str(np.round(cgndMoment,1)), fontsize=8)
            fig.text(0.1, 0.91, 'Pole : '+str(self.polecalc.at[polein,'PoleHeight'])+'-'+str(self.polecalc.at[polein,'PoleClass'])+', '+str(self.polecalc.at[polein,'PoleSpecies'])+', '+str(self.polecalc.at[polein,'GradeHeight'])+' Feet Above Grade', fontsize=8)
            fig.text(0.6, 0.985, 'Design Tension: '+ str(self.designTension) + ', Tension Overload: ' + str(self.tensionOverload), fontsize=8)
            fig.text(0.6, 0.97, 'Wind Load: ' + str(self.windLoad) + ', Wind Overload: ' + str(self.windOverload), fontsize=8)
            fig.text(0.6, 0.955, 'Strength Factor: ' + str(self.strengthFactor), fontsize=8)
            fig.text(0.6, 0.94, 'Ice Thickness: ' + str(self.iceThickness), fontsize=8)
            fig.text(0.6, 0.925, 'Deflection Factor: ' + str(self.deflectionFactor), fontsize=8)
            if rpformat=='pdf':
                plt.savefig(self.projectdir+'./PolePlots/'+polein[0]+'.pdf', dpi=None, facecolor='w', edgecolor='w',
                        orientation='portrait', papertype='letter', format='pdf',
                        transparent=False, bbox_inches='tight', pad_inches=0.5)
            else:
                plt.savefig(self.projectdir+'./PolePlots/'+polein[0]+'.png', dpi=None, facecolor='w', edgecolor='w',
                        orientation='portrait', papertype='letter', format='png',
                        transparent=False, bbox_inches='tight', pad_inches=0.5)
                
            plt.close()
            if (bgndMoment==gndMoment) and (bcgndMoment==cgndMoment):
                sqrtx=(self.polecalc.at[polein,'Mgndx']+self.polecalc.at[polein,'Mcgndx'])*(self.polecalc.at[polein,'Mgndx']+self.polecalc.at[polein,'Mcgndx'])
                sqrty=(self.polecalc.at[polein,'Mgndy']+self.polecalc.at[polein,'Mcgndy'])*(self.polecalc.at[polein,'Mgndy']+self.polecalc.at[polein,'Mcgndy'])
            elif (bgndMoment!=gndMoment) and (bcgndMoment==cgndMoment):
                sqrtx=(self.polecalc.at[polein,'Mgndx']+self.polecalc.at[polein,'Mgx']+self.polecalc.at[polein,'Mcgndx'])*(self.polecalc.at[polein,'Mgndx']+self.polecalc.at[polein,'Mgx']+self.polecalc.at[polein,'Mcgndx'])
                sqrty=(self.polecalc.at[polein,'Mgndy']+self.polecalc.at[polein,'Mgy']+self.polecalc.at[polein,'Mcgndy'])*(self.polecalc.at[polein,'Mgndy']+self.polecalc.at[polein,'Mgy']+self.polecalc.at[polein,'Mcgndy'])
            elif (bgndMoment==gndMoment) and (bcgndMoment!=cgndMoment):
                sqrtx=(self.polecalc.at[polein,'Mgndx']+self.polecalc.at[polein,'Mcgndx']+self.polecalc.at[polein,'Mcgx'])*(self.polecalc.at[polein,'Mgndx']+self.polecalc.at[polein,'Mcgndx']+self.polecalc.at[polein,'Mcgx'])
                sqrty=(self.polecalc.at[polein,'Mgndy']+self.polecalc.at[polein,'Mcgndy']+self.polecalc.at[polein,'Mcgy'])*(self.polecalc.at[polein,'Mgndy']+self.polecalc.at[polein,'Mcgndy']+self.polecalc.at[polein,'Mcgy'])
            else:
                sqrtx=(self.polecalc.at[polein,'Mgndx']+self.polecalc.at[polein,'Mgx']+self.polecalc.at[polein,'Mcgndx']+self.polecalc.at[polein,'Mcgx'])*(self.polecalc.at[polein,'Mgndx']+self.polecalc.at[polein,'Mgx']+self.polecalc.at[polein,'Mcgndx']+self.polecalc.at[polein,'Mcgx'])
                sqrty=(self.polecalc.at[polein,'Mgndy']+self.polecalc.at[polein,'Mgy']+self.polecalc.at[polein,'Mcgndy']+self.polecalc.at[polein,'Mcgy'])*(self.polecalc.at[polein,'Mgndy']+self.polecalc.at[polein,'Mgy']+self.polecalc.at[polein,'Mcgndy']+self.polecalc.at[polein,'Mcgy'])
            
            totalMoment=np.sqrt(sqrtx+sqrty)
            if (totalMoment/resistMoment)>0.8:
                guyRequired=True
            else:
                guyRequired=False
            
            self.polesummary.loc[polein[0],:]=[str(np.round(resistMoment,1)),bgndMoment,guyMoment,gndMoment,bcgndMoment,cguyMoment,cgndMoment,totalMoment,guyRequired]
            
    
    def poleLaunch(self,projectname,projectdir,designTension,strengthFactor,windLoad,windOverload,tensionOverload,iceThickness,windAngle,deflectionFactor,overrideSpan,overrideAngle):
        #Performance Warnings are not critical at this stage of developement, suppress
        warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
        
        self.projectname=projectname
        self.projectdir=projectdir
        
        if not os.path.exists(projectdir+'PolePlots/'):
            os.makedirs(projectdir+'PolePlots/')
        
        if not os.path.exists(projectdir+'PoleResults/'):
            os.makedirs(projectdir+'PoleResults/')
        
        self.designTension=designTension
        self.strengthFactor=strengthFactor
        self.windLoad=windLoad
        self.windOverload=windOverload
        self.tensionOverload=tensionOverload
        self.iceThickness=iceThickness
        self.windAngle=windAngle
        self.deflectionFactor=deflectionFactor
        self.overrideSpan=overrideSpan
        self.overrideAngle=overrideAngle
        
        self.prepData()
        self.asmCalculator(projectdir)
        self.poleCalculator()
        self.conductorCalculator()
        self.commsCalculator()
        self.poleMoments()
        self.guydb=self.guyCalculator(False)
        self.cguydb=self.guyCalculator(True)
        self.totalMomentCalculator()
        self.polePlotter('png')
        
        self.poleNocalc.filter(['PoleTag','PoleHeight','PoleClass','MapX','MapY','PoleSpecies'])
        self.poleNocalc.to_csv(projectdir+'./PoleResults/poleNocalc.csv')
        self.polecalc.to_csv(projectdir+'./PoleResults/polecalc.csv')
        self.condcalc.to_csv(projectdir+'./PoleResults/condcalc.csv')
        self.guydb.to_csv(projectdir+'./PoleResults/guycalc.csv')
        self.cguydb.to_csv(projectdir+'./PoleResults/cguycalc.csv')
        self.commdb.to_csv(projectdir+'./PoleResults/commcalc.csv')
        self.polesummary.to_csv(projectdir+'./PoleResults/polesummary.csv')
        
    def spanLaunch(self,projectname,projectdir,designTension,strengthFactor,windLoad,windOverload,tensionOverload,iceThickness,windAngle,deflectionFactor):
        #Performance Warnings are not critical at this stage of developement, suppress
        warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
        
        self.projectname=projectname
        self.projectdir=projectdir
        
        if not os.path.exists(projectdir+'PoleResults/'):
            os.makedirs(projectdir+'PoleResults/')
        
        self.designTension=designTension
        self.strengthFactor=strengthFactor
        self.windLoad=windLoad
        self.windOverload=windOverload
        self.tensionOverload=tensionOverload
        self.iceThickness=iceThickness
        self.windAngle=windAngle
        self.deflectionFactor=deflectionFactor
        
        self.prepData()
        self.asmCalculator(projectdir)
        self.poleCalculator()
        self.conductorCalculator()
        self.commsCalculator()
        self.poleMoments()
        self.guydb=self.guyCalculator(False)
        self.cguydb=self.guyCalculator(True)
        self.totalMomentCalculator()
        
        self.poledb=self.poledb.assign(MaxSpan=np);
        
        for polein in self.polecalc.index:
            sqrtx=self.polecalc.at[polein,'Mtx']*self.polecalc.at[polein,'Mtx']
            sqrty=self.polecalc.at[polein,'Mty']*self.polecalc.at[polein,'Mty']
            Mt=np.sqrt(sqrtx+sqrty)
            self.polecalc.at[polein,'MaxSpan']=(self.polecalc.at[polein,'Mr']-self.polecalc.at[polein,'Mb']-Mt)/self.polecalc.at[polein,'Mcmax']
        
        self.polecalc.to_csv(projectdir+'./PoleResults/polecalc.csv')
        self.condcalc.to_csv(projectdir+'./PoleResults/condcalc.csv')
