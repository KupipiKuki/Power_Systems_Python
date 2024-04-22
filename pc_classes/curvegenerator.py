# -*- coding: utf-8 -*-
"""
Created on Sun Jun 25 09:54:46 2023

@author: jmc53
"""
import sys
import pandas as pd
import numpy as np
from .pc_functions import testfunctions as tfn
import matplotlib.pyplot as plt

class xfmr_damage_curve:
    
    def __init__(self,fla,imp,cat=4):
        self.full_load_amps=fla
        if imp>1:
            self.impedance=imp/100
        else:
            self.impedance=imp
        self.i_2sec=self.full_load_amps/self.impedance
        
        curve=np.loadtxt('./pc_classes/pc_data/curves/xfmr.txt')
        curve[:,0]=curve[:,0]*self.full_load_amps
        
        if cat>1:
            self.curve=None
            
            if cat<4:
                cmod=np.array([0.7*self.i_2sec,4.08])
            else:
                cmod=np.array([0.5*self.i_2sec,8])
            cmod=np.vstack((cmod,np.array([self.i_2sec,2])))
            
            for row in curve:
                if row[0]<cmod[0,0]:
                    if self.curve is not None:
                        self.curve=np.vstack((self.curve,row))
                    else:
                        self.curve=row.copy()
                else:
                    break
            
            self.curve=np.vstack((self.curve,cmod))
        else:
            self.curve=curve
        

class curve_calc:
    
    def __init__(self,Ip,CT,TD,inst,delay,minresp,shift,adder,lcf,hcf,Ceq,coeff,curve=None):
        if hcf==0:
            hcf=100000
        if Ceq==5:
            self.x=1.1
        else:
            self.x=1.5
        if lcf>self.x:
            if lcf<100 and lcf < hcf:
                self.x=lcf
        self.max_x=int(100000/CT)
        if self.max_x<500:
            self.x_inc=0.01
        else:
            self.x_inc=0.1
        self.Ip=Ip
        self.CT=CT
        self.TD=TD
        self.inst=inst
        self.delay=delay
        self.minresp=minresp
        self.shift=shift
        self.adder=adder
        self.lcf=lcf
        self.hcf=hcf
        self.Ceq=Ceq
        self.coeff=coeff
        if Ceq<99:
            self.curve=self.__get_step(self.x)
        else:
            self.curve=curve
        
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

    
    def __apply_min_response(self):
        #for x in range(self.curve.shape[0]):
        #    if self.curve[x][1]<self.minresp:
        #        self.curve[x][1]=self.minresp
        self.curve[:,1]=np.where(self.curve[:,1]<self.minresp,self.minresp,self.curve[:,1])

    def get_step(self,x,delay=0):
        if delay==0:
            self.curve=np.vstack((self.curve,self.__get_step(x)))
        else:
            self.curve=np.vstack((self.curve,np.array([x*self.Ip*self.CT,delay])))
    
    def generate(self):
        if self.Ceq<99:
            while self.x <= self.max_x:
                if self.x>self.hcf:
                    break
                if self.inst>0 and self.x>=self.inst:
                    self.get_step(self.x,self.delay)
                else:
                    self.get_step(self.x)
                self.x+=self.x_inc
            if self.minresp>0:
                self.__apply_min_response()
            if self.shift>0:
                self.curve[:,0]=self.curve[:,0]*self.shift
        else:
            if self.coeff[1]>0:
                self.curve[:,0]=self.curve[:,0]*self.coeff[0]*self.Ip*self.CT
                self.curve[:,1]=self.curve[:,1]*self.TD
                if self.inst>0:
                    self.curve[:,0]=np.where(self.curve[:,1]<self.inst,self.delay,self.curve[:,1])
            else:
                self.curve[:,0]=self.curve[:,0]*self.coeff[0]*self.Ip*self.CT
            if self.minresp>0:
                self.__apply_min_response()
            if self.shift>0:
                self.curve[:,0]=self.curve[:,0]*self.shift
            if self.curve[0][0]>self.curve[-1][0]:
                self.curve=np.flipud(self.curve)

class curve_generator:
    
    def __init__(self,projectdir='./',projectname=None,ocdevdb=None):
        #csv column labels for overcurrent devices: StudyPoleTag,DevTag,CurveRef,iPickup,ctRatio,TimeDial,iPickupInst,Delay,ShowPlot,PlotLabel
        #
        #Hydraulic Recloser Note: only the base curve is included, so an iPickup of 1 and a ctRatio of 1 would refer to a 5A, a ctRatio of 3 would refer to a 15A... 
        #self.prepData()
        if projectname is not None:
            self.curvedb = pd.read_csv('./pc_classes/pc_data/curves/curvedb.csv',dtype={'CurveRef' : str, 'CurveRefAlt1' : str, 'CurveRefAlt2' : str, 'CurveFile' : str})
            
            self.project_name=projectname
            self.project_dir=projectdir
            self.faults={ 0 : [False,0,None,False],
                          1 : [False,0,None,False],
                          2 : [False,0,None,False],
                          3 : [False,0,None,False],
                          4 : [False,0,None,False]}
            
            if ocdevdb is None:
                try:
                    self.ocdevdb = pd.read_csv(self.project_dir+'ocdevdb.csv',dtype={'StudyPoleTag' : str, 'DevTag' : str})
                except FileNotFoundError:
                    print('File not found: '+self.project_dir+'ocdevdb.csv' )
                    sys.exit(1)
                except pd.io.common.EmptyDataError:
                    print('File Empty')
                    sys.exit(1)
            else:
                if type(ocdevdb) is not pd.DataFrame:
                    print('Overcurrent Device Database is not a Pandas DataFrame!')
                    sys.exit(1)
                elif ocdevdb.empty:
                    print('Overcurrent Device Database is empty!')
                    sys.exit(1)
                self.ocdevdb=ocdevdb
                    
            try:
                self.ocdevdb.columns.get_loc('StudyPoleTag')
            except KeyError:
                print('Study Pole Tag Missing')
                sys.exit(1)
                
            try:
                self.ocdevdb.columns.get_loc('DevTag')
            except KeyError:
                print('Overcurrent Device Tag Missing')
                sys.exit(1)
            
            try:
                self.ocdevdb.columns.get_loc('CurveRef')
            except KeyError:
                print('Curve Designation Missing')
                sys.exit(1)
        
            try:
                self.ocdevdb.columns.get_loc('ShowPlot')
            except KeyError:
                print('No plots to be printed, exiting...')
                sys.exit(1)
                
            col_names=['iPickup',
                       'ctRatio',
                       'TimeDial',
                       'iPickupInst',
                       'Delay',
                       'Shift',
                       'Adder',
                       'LowCurrentCutoff',
                       'HighCurrentCutoff',
                       'MinimumResponse',
                       'IsTransformer',
                       'FullLoadAmps',
                       'Impedance',
                       'Category',
                       'ShowDamage',
                       'ShowColdLoad',
                       'ShowMag']
            
            for name in col_names:
                if name not in self.ocdevdb.columns:
                    self.ocdevdb[name]=0
            
            for devnum in range(0,len(self.ocdevdb.index)):
                self.ocdevdb.iat[devnum,self.ocdevdb.columns.get_loc('ShowPlot')]=tfn.boolEvalPython(self.ocdevdb.iat[devnum,self.ocdevdb.columns.get_loc('ShowPlot')])
            
    def Add_Fault(self,num=None,enabled=True,magnitude=0,name=None,disptime=True):
        if name is not None:
            if num is not None:
                if num < 5:
                    self.faults[int(num)] = [tfn.boolEvalPython(enabled),magnitude,name,disptime]
                else:
                    self.faults[0] = [tfn.boolEvalPython(enabled),magnitude,name,disptime]
    
    def curveload(self,curveref,Ip,CT,TD,inst,delay,minresp,shift,adder=0,lcf=0,hcf=0):
        cfound=False
        for curvenum in range(0, len(self.curvedb.index)):
            if self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveRef')]==curveref:
                cfound=True
                break
            elif self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveRefAlt1')]==curveref:
                cfound=True
                break
            elif self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveRefAlt2')]==curveref:
                cfound=True
                break
        if cfound==True:
            if pd.isna(self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveFile')]):
                print('Curve Equation '+str(self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveEquation')]))
                Ceq=self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveEquation')]
                coeff=[self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveCoeff0')],
                       self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveCoeff1')],
                       self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveCoeff2')],
                       self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveCoeff3')],
                       self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveCoeff4')],
                       self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveCoeff5')],
                       self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveCoeff6')]]
                curve_data=curve_calc(Ip, CT, TD, inst, delay, minresp, shift, adder, lcf, hcf, Ceq, coeff)
            else:
                Ceq=99
                coeff=[self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveModifier')],
                       self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveAdjust')]]
                curve_data=curve_calc(Ip, CT, TD, inst, delay, minresp, shift, adder, lcf, hcf, Ceq, coeff,np.loadtxt('./pc_classes/pc_data/curves/'+self.curvedb.iat[curvenum,self.curvedb.columns.get_loc('CurveFile')]))
            curve_data.generate()
            relaycurve=curve_data.curve
            print(relaycurve[0][0],relaycurve[-1][0])
        else:
            print('Curve Not Found')
        return relaycurve
    
    def Plot_Chart(self,xlim=[10,100000]):
        pl1 = self.ocdevdb.loc[(self.ocdevdb.ShowPlot==True)]
        xfmrcurves=dict()
        plottotal=len(pl1.index)
        plotcurves=[]
        cnum=0
        if (tfn.testPositiveFloat(plottotal)):
            if plottotal>10:
                print('Plots selected: '+plottotal+' exceeds maximum, defaulting to 6')
                plottotal=10
        else:
            print('No plots to be printed, exiting...')
            sys.exit(1)
        
        for ocdev in range(0,len(pl1.index)):
            curveref=pl1.iat[ocdev,pl1.columns.get_loc('CurveRef')]
            if tfn.testIsString(curveref)==False:
                print('Convereting curve number to string\r\n')
                curveref=str(curveref)
            if not tfn.boolEvalPython(pl1.iat[ocdev,pl1.columns.get_loc('IsTransformer')]):
                devCurve=pd.DataFrame(
                    self.curveload(
                        curveref,
                        pl1.iat[ocdev,pl1.columns.get_loc('iPickup')],
                        pl1.iat[ocdev,pl1.columns.get_loc('ctRatio')],
                        pl1.iat[ocdev,pl1.columns.get_loc('TimeDial')],
                        pl1.iat[ocdev,pl1.columns.get_loc('iPickupInst')],
                        pl1.iat[ocdev,pl1.columns.get_loc('Delay')],
                        pl1.iat[ocdev,pl1.columns.get_loc('MinimumResponse')],
                        pl1.iat[ocdev,pl1.columns.get_loc('Shift')],
                        pl1.iat[ocdev,pl1.columns.get_loc('Adder')],
                        pl1.iat[ocdev,pl1.columns.get_loc('LowCurrentCutoff')],
                        pl1.iat[ocdev,pl1.columns.get_loc('HighCurrentCutoff')]),
                    columns=['Current','Time'])
                
                devCurve=devCurve.assign(CurveNum=ocdev)
                plotcurves.append(ocdev)
                devCurve.set_index('CurveNum',inplace=True)
                for key in self.faults:
                    if self.faults[key][3]:
                        pl1.iat[ocdev,pl1.columns.get_loc('PlotLabel')]=pl1.iat[ocdev,pl1.columns.get_loc('PlotLabel')]+' '+str(np.round(np.interp(self.faults[key][1],devCurve['Current'],devCurve['Time']),2))+ ' Seconds'
                if ocdev==0:
                    devCurves=devCurve
                else:
                    devCurves=pd.concat([devCurves,devCurve])
            else:
                if tfn.testPositiveFloat(pl1.iat[ocdev,pl1.columns.get_loc('FullLoadAmps')]) and tfn.testPositiveFloat(pl1.iat[ocdev,pl1.columns.get_loc('Impedance')]):
                    fla_temp=pl1.iat[ocdev,pl1.columns.get_loc('FullLoadAmps')]
                    z_temp=pl1.iat[ocdev,pl1.columns.get_loc('Impedance')]
                    if tfn.boolEvalPython(pl1.iat[ocdev,pl1.columns.get_loc('ShowDamage')]):
                        if tfn.testIsNotNumberRangeBool(pl1.iat[ocdev,pl1.columns.get_loc('Category')], 1, 4) and pl1.iat[ocdev,pl1.columns.get_loc('Impedance')]>4:
                            curve_data=xfmr_damage_curve(fla_temp, z_temp, pl1.iat[ocdev,pl1.columns.get_loc('Category')])
                        else:
                            curve_data=xfmr_damage_curve(fla_temp, z_temp)
                        xfmrcurves[cnum]=[pl1.iat[ocdev,pl1.columns.get_loc('PlotLabel')]+' Damage Curve',pd.DataFrame(curve_data.curve,columns=['Current','Time'])]
                        cnum+=1
                    if tfn.boolEvalPython(pl1.iat[ocdev,pl1.columns.get_loc('ShowColdLoad')]):
                        xfmrcurves[cnum]=[pl1.iat[ocdev,pl1.columns.get_loc('PlotLabel')]+' Cold Load Inrush',pd.DataFrame(np.array([[2*fla_temp,100],[3*fla_temp,10],[6*fla_temp,1]]),columns=['Current','Time'])]
                        cnum+=1
                    if tfn.boolEvalPython(pl1.iat[ocdev,pl1.columns.get_loc('ShowMag')]):
                        xfmrcurves[cnum]=[pl1.iat[ocdev,pl1.columns.get_loc('PlotLabel')]+' Magnetizing Inrush',pd.DataFrame(np.array([[12*fla_temp,0.1],[25*fla_temp,0.01]]),columns=['Current','Time'])]
                        cnum+=1
        fig = plt.figure(figsize=(8.5, 11), dpi=80, facecolor='w', edgecolor='k')
        ax=fig.add_subplot(111, aspect='equal')
        for ocdev in plotcurves:
            devCurves.loc[ocdev].plot(ax=ax,x='Current',y='Time',loglog=True, label=pl1.iat[ocdev,pl1.columns.get_loc('PlotLabel')])
        for xfmr in xfmrcurves.keys():
            xfmrcurves[xfmr][1].plot(ax=ax,x='Current',y='Time',loglog=True, label=xfmrcurves[xfmr][0])
        for key in self.faults:
            if self.faults[key][0]:
                ax.loglog([self.faults[key][1],self.faults[key][1]], [0.01,100],label=self.faults[key][2])
        plt.xlim(xlim[0],xlim[1])
        plt.ylim(0.01,1000)
        plt.grid
        plt.grid(b=True, which='both', color='0.65',linestyle='-')
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels, loc=1)
        ax.set_title(self.project_name+' Time Coordination Chart')
        ax.set_xlabel('Current (A)')
        ax.set_ylabel('Time (s)')
        plt.savefig(self.project_dir+self.project_name+'-TCC.pdf', dpi=None, facecolor='w', edgecolor='w',
                orientation='portrait', format='pdf',
                transparent=False, bbox_inches=None, pad_inches=0.25)
        plt.close()