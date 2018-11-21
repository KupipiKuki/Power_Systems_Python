# -*- coding: utf-8 -*-
"""
Created on Wed Feb 05 08:31:22 2014

@author: jcheers
"""

import numpy as np
import scipy as sp
from math import pi
from math import log
from math import sqrt
import scipy.stats as ssp

import conductorvals as conddata
import constantvals as cval
import towervals as towerdata


def calc_current(material,name,tempamb,temprise):
	#most conductors rated at 25C
    ratedamb=25
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
    
    if material=='AAC':
		#set conductortype to All Aluminum Conductor
        conductortype=2
        rows=len(conddata.AAC)
        for il in range(rows):
            if conddata.AAC[il]==name:
                conductorname=il
                ratedrise=conddata.AACtemp[conductorname]-ratedamb
                #ratedcurrent=conddata.AACcurrent[conductorname];
				#Get the geomatric mean radius of the conductor
                gmrval = conddata.AACgmr[conductorname]
				#AC resistance per mile
                acohmval = conddata.AACohms[conductorname]
				#AC resistance per mile
                dcohmval = conddata.AACDCohms[conductorname]
    elif material=='ACSR':
        conductortype=3
        rows=len(conddata.ACSR)
        for il in range(rows):
            if conddata.ACSR[il]==name:
                conductorname=il
                ratedrise=conddata.ACSRtemp[conductorname]-ratedamb
                #ratedcurrent=conddata.ACSRcurrent[conductorname];
                gmrval = conddata.ACSRgmr[conductorname]
                acohmval = conddata.ACSRohms[conductorname]
                dcohmval = conddata.ACSRDCohms[conductorname]
    elif material=='ACCC':
        conductortype=4
        rows=len(conddata.ACCC)
        for il in range(rows):
            if conddata.ACCC[il]==name:
                conductorname=il
                ratedrise=conddata.ACCCtemp[conductorname]-ratedamb
                #ratedcurrent=conddata.ACCCcurrent[conductorname];
                gmrval = conddata.ACCCgmr[conductorname]
                acohmval = conddata.ACCCohms[conductorname]
                dcohmval = conddata.ACCCDCohms[conductorname]
    else:
        conductortype=1
        rows=len(conddata.Copper)
        for il in range(rows):
            if conddata.Copper[il]==name:
                conductorname=il
                ratedrise=conddata.Coppertemp[conductorname]-ratedamb
                #ratedcurrent=conddata.Coppercurrent[conductorname];
                gmrval = conddata.Coppergmr[conductorname]
                acohmval = conddata.Copperohms[conductorname]
                dcohmval = conddata.CopperDCohms[conductorname]
    
	#DC resistance per foot
    resdc=dcohmval/5280
	#AC resistance per foot
    resac=acohmval/5280
    #radius in inches
    radius=gmrval*12
    #area of the wire in ft
    surfaceareaft=2*pi*gmrval
    #area of the wire for 12 inches
    surfaceareain=2*pi*radius*12
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
        wc=0.283*sqrt(pf)*(radius*2)**0.75*(temprise)**1.25
    else:
        wc1=(1.01+0.371*((pf*windval*60*60*radius*2)/uf)**0.52)*kf*(temprise)
        wc2=(0.1695*((pf*windval*60*60*radius*2)/uf)**0.6)*kf*(temprise)
        wc=max(wc1,wc2)
    #Angle of the Sun in radians
    angle=(sunaltitude*pi/180)
    #Solar Heat Gain, W/ft
    ws=0.5*sunintensity*np.sin(np.arccos(np.cos(angle)*np.cos((sunazimuth*pi/180)-(condazimuth*pi/180))))*surfaceareaft
    #Maximum Solar Heat Gain, W/ft
    wsbase=0.5*100*np.sin(90*pi/180)*surfaceareaft
    #Losses in W/in2-ft
    powerloss=(wc+wr)/surfaceareain
    #Conductor Resistance Calculations
    if conductortype==4:
        resac=resdc+((resac-resdc)/(75-25))*(tempcond-25)
    elif conductortype==1:
        resdctemp=resdc*(1+0.00381*((ratedamb+ratedrise)-20))
        resacdc=resac/resdctemp
        resdc=resdc*(1+0.00381*((tempamb+temprise)-20))
        resac=resdc*resacdc
    else:
        resdctemp=resdc*(1+0.00403*((ratedamb+ratedrise)-20))
        resacdc=resac/resdctemp
        resdc=resdc*(1+0.00403*((tempamb+temprise)-20))
        resac=resdc*resacdc
    ohmval=(resac*5280)
    #Calculates the base current before accounting for sun and wind
    currentbase=sqrt((37.7*radius*2*powerloss)/resac)
    if ws==0:
        current=currentbase
    else:
        if windval>0:
            current=currentbase*(0.99-((0.05*radius*2)*(ws/wsbase)))
        else:
            current=currentbase*(0.99-(0.07*(angle/(pi/2)))-((0.05*radius*2)*(ws/wsbase)))
    
    return ohmval, gmrval, current

def tower_calc(towername):
    rows=len(towerdata.TOWERMAT)
    for il in range(rows):
        if towerdata.TOWERMAT[il]==towername:
            if il<4:
                tdat=towerdata.VA11
                break
            elif il<8:
                tdat=towerdata.VA11P
                break
            elif il<10:
                tdat=towerdata.VA111
                break
            elif il<12:
                tdat=towerdata.VA111P
                break
            elif il<15:
                tdat=towerdata.VB111
                break
            elif il<18:
                tdat=towerdata.VB111P
                break
            elif il<19:
                tdat=towerdata.VB114
                break
            elif il<20:
                tdat=towerdata.VB114P
                break
            elif il<23:
                tdat=towerdata.VC111
                break
            elif il<26:
                tdat=towerdata.VC111P
                break
            elif il<27:
                tdat=towerdata.VC141
                break
            elif il<28:
                tdat=towerdata.VC141L
                break
            elif il<29:
                tdat=towerdata.VC141P
                break
            elif il<30:
                tdat=towerdata.VC252
                break
            elif il<31:
                tdat=towerdata.VC252L
                break
            elif il<33:
                tdat=towerdata.C11NP
                break
            elif il<34:
                tdat=towerdata.C141
                break
            elif il<35:
                tdat=towerdata.C2VNP
                break
            elif il<36:
                tdat=towerdata.C2VNPA
                break
            elif il<37:
                tdat=towerdata.C2VNPB
                break
            elif il<38:
                tdat=towerdata.C2VNPBR
                break
            elif il<39:
                tdat=towerdata.C2VNPR
                break
            elif il<40:
                tdat=towerdata.TP69
                break
            elif il<42:
                tdat=towerdata.TP69BC
                break
            elif il<43:
                tdat=towerdata.TP69G
                break
            elif il<45:
                tdat=towerdata.TP69GB
                break
            elif il<49:
                tdat=towerdata.TP1234
                break
            elif il<53:
                tdat=towerdata.TP1234A
                break
            elif il<54:
                tdat=towerdata.TPS1
                break
            elif il<56:
                tdat=towerdata.TS12
                break
            elif il<58:
                tdat=towerdata.TS12X
                break
            elif il<59:
                tdat=towerdata.TS1B
                break
            elif il<61:
                tdat=towerdata.TS1BXC
                break
            elif il<62:
                tdat=towerdata.TS1L
                break
            elif il<63:
                tdat=towerdata.TS1LX
                break
            elif il<64:
                tdat=towerdata.TS9
                break
            elif il<66:
                tdat=towerdata.TSS12
                break
            elif il<68:
                tdat=towerdata.TSS1BC
                break
            elif il<69:
                tdat=towerdata.TSS1L
                break
            elif il<70:
                tdat=towerdata.TSS9
                break
            elif il<72:
                tdat=towerdata.TSZ12
                break
            elif il<73:
                tdat=towerdata.TU1
                break
            elif il<74:
                tdat=towerdata.TU1A
                break
            elif il<75:
                tdat=towerdata.TU1AA
                break
            elif il<80:
                tdat=towerdata.TS345A
                break
            elif il<85:
                tdat=towerdata.TS345AG
                break
            elif il<86:
                tdat=towerdata.TH1
                break
            elif il<87:
                tdat=towerdata.TH1G
                break
            elif il<89:
                tdat=towerdata.TH1CX
                break
            elif il<91:
                tdat=towerdata.TH1CGX
                break
            elif il<94:
                tdat=towerdata.TH345
                break
            elif il<96:
                tdat=towerdata.TH34G
                break
            elif il<97:
                tdat=towerdata.TH5G
                break
            elif il<98:
                tdat=towerdata.THD
                break
            elif il<99:
                tdat=towerdata.TH5GD
                break
            elif il<100:
                tdat=towerdata.TH7
                break
            elif il<101:
                tdat=towerdata.TH7G
                break
            elif il<102:
                tdat=towerdata.TH9
                break
            elif il<103:
                tdat=towerdata.TH9G
                break
            else:
                tdat=towerdata.VC111
                break
    return tdat
#Conductor Type,
#Conductor Name,
#Length of Line,
#Length Units (miles-0,kilometers-1),
#Neutral Conductor Type,
#Neutral Conductor Name,
#Soil Type (wet-1,swampy-2,average-3,dry-4),
#Ambient Temperature (Celsius),
#Conductor Temperature Rise (Celsius),
#Frequency,
#Tower Name,
#Transposition 1 %,
#Transposition 2 %,
#Transposition 3 %,
def calcimpedance(material, name, length, units, nmaterial, nname, environmenttype, tempamb, temprise,f,towername,tp1,tp2,tp3):
    
    gmd=tower_calc(towername)
    linetype=gmd[22,0]
    neutral=gmd[22,1]
    gmd=gmd*(1.0/12.0)
    ohmval, gmrval, current=calc_current(material,name,tempamb,temprise)
    nohmval, ngmrval, ncurrent=calc_current(nmaterial,nname,tempamb,temprise)
    #Length Units (miles-0,kilometers-1)
    if units==1:
        res = ohmval*0.6213712
        gmr = gmrval
        resN = nohmval*0.6213712
        gmrN = ngmrval
        w = 1.2566e-3
        resd = 9.869e-4*f
    else:
        res = ohmval
        gmr = gmrval
        resN = nohmval
        gmrN = ngmrval
        w = 2.0224e-3
        resd = 1.588e-3*f
    #Assume second neutral is the same material and size as first
    res2N=resN
    gmr2N=gmrN
    #Soil Type (wet-1,swampy-2,average-3,dry-4)
    if environmenttype==1:
        De=27.9
    elif environmenttype==2:
        De=882
    elif environmenttype==3:
        De=2790
    else:
        De=8820
    
    zs=res+resd+1j*w*f*log(De/gmr)
    
    #Check to see phase configuration (determined by tower)
    if linetype==3:
        f1=tp1/(tp1+tp2+tp3)
        f2=tp2/(tp1+tp2+tp3)
        f3=tp3/(tp1+tp2+tp3)
        fmat=sp.mat([[f1,f2,f3],
                     [f3,f1,f2],
                     [f2,f3,f1]])
        zk=resd+1j*w*f*sp.mat([log(De/gmd[0,0]),log(De/gmd[0,1]),log(De/gmd[0,2])])*fmat
        zabc=sp.mat([[zs, zk[0,0], zk[0,2]], [zk[0,0], zs, zk[0,1]], [zk[0,2], zk[0,1], zs]])
        
        if neutral>1:
            zsn=sp.mat([[resN+resd+1j*w*f*log(De/gmrN),resd+1j*w*f*log(De/gmd[4,0])],
                        [resd+1j*w*f*log(De/gmd[4,0]),res2N+resd+1j*w*f*log(De/gmr2N)]])
            zkn=sp.mat([[resd+1j*w*f*log(De/gmd[1,0]),resd+1j*w*f*log(De/gmd[1,1]),resd+1j*w*f*log(De/gmd[1,2])],
                        [resd+1j*w*f*log(De/gmd[2,0]),resd+1j*w*f*log(De/gmd[2,1]),resd+1j*w*f*log(De/gmd[2,2])]])*fmat
            zabc=zabc-zkn.T*zsn.I*zkn
            
        elif neutral>0:
            zsn=resN+resd+1j*w*f*log(De/gmrN)
            zkn=sp.mat([resd+1j*w*f*log(De/gmd[1,0]),resd+1j*w*f*log(De/gmd[1,1]),resd+1j*w*f*log(De/gmd[1,2])])*fmat
            zabc=zabc-zkn.T*(1.0/zsn)*zkn
        
    elif linetype==2:
        f1=tp1/(tp1+tp2)
        f2=tp2/(tp1+tp2)
        fmat2=sp.mat([[f1,f2,0],
                      [f2,f1,0],
                      [0,0,0]])
        zk=resd+1j*w*f*log(De/gmd[0,0])
        zabc=sp.mat([[zs,zk,0],[zk,zs,0],[0,0,0]])
    
        if neutral>0:
            zsn=resN+resd+1j*w*f*log(De/gmrN)
            zkn=sp.mat([resd+1j*w*f*log(De/gmd[1,0]),resd+1j*w*f*log(De/gmd[1,1]),0])*fmat2
            zabc=zabc-zkn.T*(1.0/zsn)*zkn
    else:
        zabc=sp.mat([[zs,0,0],[0,0,0],[0,0,0]])
    
        if neutral>0:
            zsn=resN+resd+1j*w*f*log(De/gmrN)
            zkn=resd+1j*w*f*log(De/gmd[1,0])
            zabc[0,0]=zs-(zkn*zkn)/zsn
    #Multiple Zabc matrix by line length
    zabc = zabc*length
    #Perform the transformation on Zabc to obtain the sequence impedance matrix Z012
    z012 = cval.Ainv*zabc*cval.Amat
    #za=zabc[0,0]+zabc[0,1]+zabc[0,2]
    #zb=zabc[1,0]+zabc[1,1]+zabc[1,2]
    #zc=zabc[2,0]+zabc[2,1]+zabc[2,2]
    #Compute the zero sequence impedance
    z0=z012[0,0]+z012[0,1]+z012[0,2]
    #Compute the positive sequence impedance
    z1=z012[1,0]+z012[1,1]+z012[1,2]
    #zmatrix=np.array([[z1.real,z1.imag],
    #                [z0.real,z0.imag]])
    zmatrix=np.array([[z1],[z0]])
    return zmatrix

def ifault(zlt,vf,zgnd,zfault):
    zt=zlt[0,0]
    z0t=zlt[1,0]
    
    Amat=sp.array([[1, 1, 1], [1, cval.a**2, cval.a], [1, cval.a, cval.a**2]])
    
    #Phase to Ground Fault, (A-G)
    #Generate Phase Current Matrix From Sequence Current Matrix
    I012=sp.array([[(vf/(z0t+zt+zt+zfault+(3*zgnd)))],
                   [(vf/(z0t+zt+zt+zfault+(3*zgnd)))],
                   [(vf/(z0t+zt+zt+zfault+(3*zgnd)))]])
    Iabc=sp.dot(Amat,I012)
    Iseq=I012
    #I012=comp1*I012
    I012=np.multiply(cval.compd,I012)
    IabcD=sp.dot(Amat,I012)
    IseqD=I012
    #Phase to Phase Fault, (BC)
    #Generate Phase Current Matrix From Sequence Current Matrix
    I012=sp.array([[0],
    			   [(vf/(zt+zt+(zfault)))],
    			   [-vf/(zt+zt+(zfault))]])
    Iabc=sp.vstack((Iabc,sp.dot(Amat,I012)))
    Iseq=sp.vstack((Iseq,I012))
    I012=np.multiply(cval.compd,I012)
    IabcD=sp.vstack((IabcD,sp.dot(Amat,I012)))
    IseqD=sp.vstack((IseqD,I012))
    #Phase to Phase to Ground Fault, (BC-G)
    #Calculate Positive Sequence Impedance Equation
    I1=vf/((zt+zfault)+(((zt+zfault)*(z0t+(3*zgnd)))/(zt+z0t+(3*zgnd))))
    #Generate Phase Current Matrix From Sequence Current Matrix
    I012=sp.array([[(-I1*((zt+zfault)/(zt+z0t+zfault+(3*zgnd))))],
    			   [I1],
    			   [(-I1*((z0t+zfault+(3*zgnd))/(zt+z0t+(2*zfault)+(3*zgnd))))]])
    Iabc=sp.vstack((Iabc,sp.dot(Amat,I012)))
    Iseq=sp.vstack((Iseq,I012))
    I012=np.multiply(cval.compd,I012)
    IabcD=sp.vstack((IabcD,sp.dot(Amat,I012)))
    IseqD=sp.vstack((IseqD,I012))
    #Three Phase to Ground Fault
    #Calculate Positive Sequence Impedance Equation
    I1=(vf/(zt+zfault+zgnd))
    I012=sp.array([[0],[I1],[0]])
    Iabc=sp.vstack((Iabc,sp.dot(Amat,I012)))
    Iseq=sp.vstack((Iseq,I012))
    I012=np.multiply(cval.compd,I012)
    IabcD=sp.vstack((IabcD,sp.dot(Amat,I012)))
    IseqD=sp.vstack((IseqD,I012))
    Iabc=sp.vstack((Iabc,Iseq))
    
    return Iabc

#xfmr(Transformer Base MVA,
#     Transformer Base KV,
#     Nameplate Percent Impedance,
#     X/R ratio,
#     Z1/Z0 ratio)
def xfmr(MVAbase, Zpercent, XRratio, zeromult):
    #Calculate Positive Sequence Per Unit Impedance From Percent Impedance and X/R Ratio
    z1=(Zpercent/100)
    #Calculate Positive Sequence Resistance From Percent Impedance and X/R Ratio
    r1=z1/sqrt(1+XRratio**2);
    #Calculate Positive Sequence Reactance From Percent Impedance and X/R Ratio
    x1=1j*r1*XRratio
    #Calculate Zero Sequence Resistance
    r0=r1*zeromult
    #Calculate Zero Sequence Reactance
    x0=x1*zeromult
    #Returns impedance matrix:
    z1=r1+x1
    z0=r0+x0
    return sp.array([[z1],[z0]])

def xrcalc(MVAbase,results):
    if results=='low':
        if MVAbase>=12:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*(2-1.677)
        elif MVAbase>=2.5:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*(2-1.5)
        elif MVAbase>=0.5:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*(2-1.3)
        else:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])
    elif results=='high':
        if MVAbase>=12:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*1.677
        elif MVAbase>=2.5:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*1.5
        elif MVAbase>=0.5:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*1.3
        else:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])
    elif results=='rlow':
        if MVAbase>=12:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*(1-abs(1-ssp.norm.rvs(loc=1,scale=(0.677/3))))
        elif MVAbase>=2.5:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*(1-abs(1-ssp.norm.rvs(loc=1,scale=(0.5/3))))
        elif MVAbase>=0.5:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*(1-abs(1-ssp.norm.rvs(loc=1,scale=(0.3/3))))
        else:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])
    elif results=='rhigh':
        if MVAbase>=12:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*(1+abs(1-ssp.norm.rvs(loc=1,scale=(0.677/3))))
        elif MVAbase>=2.5:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*(1+abs(1-ssp.norm.rvs(loc=1,scale=(0.5/3))))
        elif MVAbase>=0.5:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*(1+abs(1-ssp.norm.rvs(loc=1,scale=(0.3/3))))
        else:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])
    elif results=='rand':
        if MVAbase>=12:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*ssp.norm.rvs(loc=1,scale=(0.677/3))
        elif MVAbase>=2.5:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*ssp.norm.rvs(loc=1,scale=(0.5/3))
        elif MVAbase>=0.5:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])*ssp.norm.rvs(loc=1,scale=(0.3/3))
        else:
            XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])
    else:
        XRratio=np.interp(MVAbase,cval.xrcurve[:,0],cval.xrcurve[:,1])
    return XRratio

def abcseq(abcmat):
    seqmat=cval.Ainv*abcmat*cval.Amat
    
    return seqmat
    
def abc2seq(abc):
    seq=sp.dot(cval.Ainv,abc)
    return seq
    
def seq2abc(seq):
    abc=sp.dot(cval.Amat,seq)
    return abc

def dy1(ID):
    I012=sp.dot(cval.Ainv,ID)
    I012Y=np.multiply(cval.compy,I012)
    IY=sp.dot(cval.Amat,I012Y)   
    return IY

def yd1(IY):
    I012=sp.dot(cval.Ainv,IY)
    I012D=np.multiply(cval.compd,I012)
    ID=sp.dot(cval.Amat,I012D)
    return ID
