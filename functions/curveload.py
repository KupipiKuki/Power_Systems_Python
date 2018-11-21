# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 10:37:10 2013

@author: jcheers
"""

import TCCcurve as tcc
import numpy as np
import matplotlib.pyplot as plt

#Ip-pickup current
#CT-current transformer ratio
#TD-Time Dial
#ratio-adjustments for files not starting at 1 amp
#inst-instantaneous pickup
#delay-time delay for instantaneous
def curveload(curveref,Ip,CT,TD,ratio,inst,delay):
    numfiles=len(tcc.curvefile)#size(tcc.curvefile)
    i1=0
    for curve in tcc.curvetype:
        if curve==curveref:
            if i1<numfiles:
                relaycurve=np.loadtxt(tcc.curvefile[i1])
                #print(relaycurve)
                if i1<67:
                    relaycurve[:,0]=relaycurve[:,0]*Ip*CT*ratio
                elif i1<111:
                    relaycurve[:,0]=(relaycurve[:,0]/100)*Ip*CT*ratio
                else:
                    relaycurve[:,0]=relaycurve[:,0]*Ip*CT*ratio
                break
            else:
                rownum=i1-numfiles
                if rownum<11:
                    x=1.5
                    if inst>0:
                        while x <= 100:
                            if x==1.5:
                                relaycurve = np.array([x*Ip*CT*ratio,TD*(tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))])
                            else:
                                if x<=(inst/Ip):
                                    relaycurve = np.vstack((relaycurve,np.array([x*Ip*CT*ratio,TD*(tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))])))
                                else:
                                    relaycurve = np.vstack((relaycurve,np.array([x*Ip*CT*ratio,delay])))
                            x+=0.1
                    else:
                        while x <= 100:
                            if x==1.5:
                                relaycurve = np.array([x*Ip*CT*ratio,TD*(tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))])
                            else:
                                relaycurve = np.vstack((relaycurve,np.array([x*Ip*CT*ratio,TD*(tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))])))
                            x+=0.1
                else:
                    x=1.5
                    if inst>0:
                        while x <= 100:
                            if x==1.5:
                                relaycurve = np.array([x*Ip*CT*ratio,((tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))*(((tcc.tccCoef[rownum,4]*TD)-tcc.tccCoef[rownum,5])/tcc.tccCoef[rownum,6]))])
                            else:
                                if x<=(inst/Ip):
                                    relaycurve = np.vstack((relaycurve,np.array([x*Ip*CT*ratio,((tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))*(((tcc.tccCoef[rownum,4]*TD)-tcc.tccCoef[rownum,5])/tcc.tccCoef[rownum,6]))])))
                                else:
                                    relaycurve = np.vstack((relaycurve,np.array([x*Ip*CT*ratio,delay])))
                            x+=0.1
                    else:
                        while x <= 100:
                            if x==1.5:
                                relaycurve = np.array([x*Ip*CT*ratio,((tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))*(((tcc.tccCoef[rownum,4]*TD)-tcc.tccCoef[rownum,5])/tcc.tccCoef[rownum,6]))])
                            else:
                                relaycurve = np.vstack((relaycurve,np.array([x*Ip*CT*ratio,((tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))*(((tcc.tccCoef[rownum,4]*TD)-tcc.tccCoef[rownum,5])/tcc.tccCoef[rownum,6]))])))
                            x+=0.1
                break
        else:
            relaycurve=np.loadtxt(tcc.curvefile[0])
            relaycurve[:,0]=relaycurve[:,0]*Ip*CT*ratio
        i1+=1
    return relaycurve

def curveloadmat(relaydb):
    curveref,Ip,CT,TD,ratio,inst,delay=relaydb
    numfiles=len(tcc.curvefile)#size(tcc.curvefile)
    i1=0
    for curve in tcc.curvetype:
        if curve==curveref:
            if i1<numfiles:
                relaycurve=np.loadtxt(tcc.curvefile[i1])
                #print(relaycurve)
                if i1<67:
                    relaycurve[:,0]=relaycurve[:,0]*Ip*CT*ratio
                elif i1<111:
                    relaycurve[:,0]=(relaycurve[:,0]/100)*Ip*CT*ratio
                else:
                    relaycurve[:,0]=relaycurve[:,0]*Ip*CT*ratio
                break
            else:
                rownum=i1-numfiles
                if rownum<11:
                    x=1.5
                    if inst>0:
                        while x <= 100:
                            if x==1.5:
                                relaycurve = np.array([x*Ip*CT*ratio,TD*(tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))])
                            else:
                                if x<=(inst/Ip):
                                    relaycurve = np.vstack((relaycurve,np.array([x*Ip*CT*ratio,TD*(tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))])))
                                else:
                                    relaycurve = np.vstack((relaycurve,np.array([x*Ip*CT*ratio,delay])))
                            x+=0.1
                    else:
                        while x <= 100:
                            if x==1.5:
                                relaycurve = np.array([x*Ip*CT*ratio,TD*(tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))])
                            else:
                                relaycurve = np.vstack((relaycurve,np.array([x*Ip*CT*ratio,TD*(tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))])))
                            x+=0.1
                else:
                    x=1.5
                    if inst>0:
                        while x <= 100:
                            if x==1.5:
                                relaycurve = np.array([x*Ip*CT*ratio,((tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))*(((tcc.tccCoef[rownum,4]*TD)-tcc.tccCoef[rownum,5])/tcc.tccCoef[rownum,6]))])
                            else:
                                if x<=(inst/Ip):
                                    relaycurve = np.vstack((relaycurve,np.array([x*Ip*CT*ratio,((tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))*(((tcc.tccCoef[rownum,4]*TD)-tcc.tccCoef[rownum,5])/tcc.tccCoef[rownum,6]))])))
                                else:
                                    relaycurve = np.vstack((relaycurve,np.array([x*Ip*CT*ratio,delay])))
                            x+=0.1
                    else:
                        while x <= 100:
                            if x==1.5:
                                relaycurve = np.array([x*Ip*CT*ratio,((tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))*(((tcc.tccCoef[rownum,4]*TD)-tcc.tccCoef[rownum,5])/tcc.tccCoef[rownum,6]))])
                            else:
                                relaycurve = np.vstack((relaycurve,np.array([x*Ip*CT*ratio,((tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))*(((tcc.tccCoef[rownum,4]*TD)-tcc.tccCoef[rownum,5])/tcc.tccCoef[rownum,6]))])))
                            x+=0.1
                break
        else:
            relaycurve=np.loadtxt(tcc.curvefile[0])
            relaycurve[:,0]=relaycurve[:,0]*Ip*CT*ratio
        i1+=1
    return relaycurve