# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 10:37:10 2013

@author: jcheers
"""

import TCCcurve as tcc
import numpy as np

#Ip-pickup current
#CT-current transformer ratio
#TD-Time Dial
#ratio-adjustments for files not starting at 1 amp
#inst-instantaneous pickup
#delay-time delay for instantaneous
def gettriptime(curvedata,Ival):
    numfiles=len(tcc.curvefile)#size(tcc.curvefile)
    i1=0
    for curve in tcc.curvetype:
        if curve==curvedata[0]:
            if i1<numfiles:
                relaycurve=np.loadtxt(tcc.curvefile[i1])
                #print(relaycurve)
                if i1<67:
                    relaycurve[:,0]=relaycurve[:,0]*curvedata[1]*curvedata[2]*curvedata[4]
                elif i1<111:
                    relaycurve[:,0]=(relaycurve[:,0]/100)*curvedata[1]*curvedata[2]*curvedata[4]
                else:
                    relaycurve[:,0]=relaycurve[:,0]*curvedata[1]*curvedata[2]*curvedata[4]
                tript=np.interp(Ival,relaycurve[:,0],relaycurve[:,1])
                print(tcc.curvefile[i1])
                break
            else:
                rownum=i1-numfiles
                if rownum<11:
                    x=Ival/(curvedata[1]*curvedata[2]*curvedata[4])
                    if curvedata[5]>0:
                        if x<=(curvedata[5]/curvedata[1]):
                            tript=curvedata[3]*(tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))
                        else:
                            tript=curvedata[6]
                    else:
                        tript=curvedata[3]*(tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))
                else:
                    if curvedata[5]>0:
                        if x<=(curvedata[5]/curvedata[1]):
                            tript=((tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))*(((tcc.tccCoef[rownum,4]*curvedata[3])-tcc.tccCoef[rownum,5])/tcc.tccCoef[rownum,6]))
                        else:
                            tript=curvedata[6]
                    else:
                        tript=((tcc.tccCoef[rownum,0]+(tcc.tccCoef[rownum,1]/(x**tcc.tccCoef[rownum,2]-tcc.tccCoef[rownum,3])))*(((tcc.tccCoef[rownum,4]*curvedata[3])-tcc.tccCoef[rownum,5])/tcc.tccCoef[rownum,6]))
                break
        else:
            relaycurve=np.loadtxt(tcc.curvefile[0])
            relaycurve[:,0]=relaycurve[:,0]*curvedata[1]*curvedata[2]*curvedata[4]
        i1+=1
    return tript
