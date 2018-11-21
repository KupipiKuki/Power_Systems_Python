# -*- coding: utf-8 -*-
"""
Created on Thu Feb 06 14:39:31 2014

@author: jcheers
"""
import numpy as np
from math import exp
import matplotlib.pyplot as plt

def flip_bit( oldval,bitnum):
    newval=oldval^bitnum
    return newval

def init_sys():
    print('stuff')

def coordination(foldername,chartname,faulttype,ip,fuse,fuse2,fcurve,dcurve,fshot,dshot,pshot,pshot2,fdelay,ddelay,ifcurrent):
    #variable initialization
    delay=0
    shot=fshot+dshot
    ftimer=0.0
    ftimer2=0.0
    fstimer=0.0
    fstimer2=0.0
    frtimer=0.0
    drtimer=0.0
    stimer=0.0
    ctimer=0.0
    finit=0
    finit2=0
    fcinit=0
    dcinit=0
    tripmat=0x00
    
    #data container init
    ttime=np.array([])
    ifault=np.array([])
    ftime=np.array([])
    ftimemat=np.array([])
    ftime2=np.array([])
    ftimemat2=np.array([])
    fctime=np.array([])
    fctimemat=np.array([])
    dctime=np.array([])
    dctimemat=np.array([])
    tripnames=np.array([])
    triptimes=np.array([])
    
    datafile=open(foldername+chartname+'-SOE.txt', 'w+') 
    datafile.write(chartname+' Sequence of Events\n')
    datafile.write('Fast Recloser Shots: '+repr(fshot)+'\n')
    datafile.write('Delayed Recloser Shots: '+repr(dshot)+'\n')
    if pshot>0:
        datafile.write('First Sectionalizer Shots: '+repr(pshot)+'\n')
    if pshot2>0:
        datafile.write('Second Sectionalizer Shots: '+repr(pshot2)+'\n')
    datafile.write('\n')
    time=range(1,50000)
    #timercap=np.array([np.random.rand(1)*200/1000,
    #                   np.random.rand(1)*200/1000,
    #                   np.random.rand(1)*200/1000,
    #                   np.random.rand(1)*200/1000,
    #                   np.random.rand(1)*200/1000])
    timercap=np.array([0.03, 0.03,0.03,0.1,0.5])
    timerind=0
    for t in time:
        current=ifcurrent*(1-exp(-ctimer/40.0))
        timer=t/1000.0
        ttime=np.append(ttime,timer)
        ifault=np.append(ifault,current)
        if delay==0:
            ctimer+=1
            if current>fuse[0,0]:
                finit=1
                ftimer+=(1/1000.0)
                fstimer+=(1/1000.0)
                ftime=np.append(ftime,np.interp(current,fuse[:,0],fuse[:,1]))
                ftimemat=np.append(ftimemat,timer)
            if current>fuse2[0,0]:
                finit2=1
                ftimer2+=(1/1000.0)
                fstimer2+=(1/1000.0)
                ftime2=np.append(ftime2,np.interp(current,fuse2[:,0],fuse2[:,1]))
                ftimemat2=np.append(ftimemat2,timer)
            if current>ip:
                stimer+=(1/1000.0)
                if fshot>0:
                    fcinit=1
                    frtimer+=(1/1000.0)
                    fctime=np.append(fctime,np.interp(current,fcurve[:,0],fcurve[:,1]))
                    fctimemat=np.append(fctimemat,timer)
                else:
                    dcinit=1
                    drtimer+=(1/1000.0)
                    dctime=np.append(dctime,np.interp(current,dcurve[:,0],dcurve[:,1]))
                    dctimemat=np.append(dctimemat,timer)
                current=0
        else:
            delay-=1
        if faulttype>0:
            if (ctimer/1000.0)>timercap[timerind]:
                timerind+=1
                if timerind>4:
                    timerind=0
                delay=timercap[timerind]*1000
                fstimer=0
                fstimer2=0
                stimer=0
                ctimer=0
                
        if finit==1:
            if fstimer>=ftime[ftimer*1000-1]:
                print('fuse 1 blown at '+repr(timer)+' seconds')
                datafile.write('fuse 1 blown at '+repr(timer)+' seconds\n')
                tripnames=np.append(tripnames,'Fuse 1 Trip')
                triptimes=np.append(triptimes,timer)
                break
        if finit2==1:
            if fstimer2>=ftime2[ftimer2*1000-1]:
                print('fuse 2 blown at '+repr(timer)+' seconds')
                datafile.write('fuse 2 blown at '+repr(timer)+' seconds\n')
                tripnames=np.append(tripnames,'Fuse 2 Trip')
                triptimes=np.append(triptimes,timer)
                break
        if dcinit==1:
            if stimer>=dctime[drtimer*1000-1]:
                if fshot==0:
                    if dshot>0:
                        print('Recloser Delayed Curve Trip at '+repr(timer)+' seconds')
                        datafile.write('Recloser Delayed Curve Trip at '+repr(timer)+' seconds\n')
                        tripnames=np.append(tripnames,'Delayed Trip')
                        triptimes=np.append(triptimes,timer)
                        dshot-=1
                        delay=ddelay
                        fstimer=0
                        fstimer2=0
                        stimer=0
                        ctimer=0
                        if pshot>0:
                            pshot-=1
                        if pshot2>0:
                            pshot2-=1
        if fcinit==1:
            if stimer>=fctime[frtimer*1000-1]:
                if fshot>0:
                    print('Recloser Fast Curve Trip at '+repr(timer)+' seconds')
                    datafile.write('Recloser Fast Curve Trip at '+repr(timer)+' seconds\n')
                    tripnames=np.append(tripnames,'Fast Trip')
                    triptimes=np.append(triptimes,timer)
                    fshot-=1
                    delay=fdelay
                    fstimer=0
                    fstimer2=0
                    stimer=0
                    ctimer=0
                    if pshot>0:
                        pshot-=1
                    if pshot2>0:
                        pshot2-=1
        
        shot=fshot+dshot
        if shot==0:
            print('Recloser Lockout at '+repr(timer)+' seconds')
            datafile.write('Recloser Lockout at '+repr(timer)+' seconds\n')
            tripnames=np.append(tripnames,'Lockout')
            triptimes=np.append(triptimes,timer)
            break
        if pshot==0:
            print('Sectionalizer 1 Open at '+repr(timer)+' seconds')
            datafile.write('Sectionalizer 1 Open at '+repr(timer)+' seconds\n')
            tripnames=np.append(tripnames,'Sectionalizer 1')
            triptimes=np.append(triptimes,timer)
            break
        if pshot2==0:
            print('Sectionalizer 2 Open at '+repr(timer)+' seconds')
            datafile.write('Sectionalizer 2 Open at '+repr(timer)+' seconds\n')
            tripnames=np.append(tripnames,'Sectionalizer 2')
            triptimes=np.append(triptimes,timer)
            break
    fig,ax=plt.subplots(2, sharex=True)
    if fcinit==1:
        ax[0].scatter(fctimemat,fctime,color='red',marker='.',label='fast curve')
        del fctime,fctimemat
    if finit==1:
        ax[0].scatter(ftimemat,ftime,color='green',marker='.',label='fuse 1')
        del ftime,ftimemat
    if finit2==1:
        ax[0].scatter(ftimemat2,ftime2,color='orange',marker='.',label='fuse 2')
        del ftime2,ftimemat2
    if dcinit==1:
        ax[0].scatter(dctimemat,dctime,color='blue',marker='.',label='delayed curve')
        del dctime,dctimemat
    ax[0].set_ylim(0,2)
    handles, labels = ax[0].get_legend_handles_labels()
    ax[0].legend(handles, labels)
    ax[0].set_title(chartname+' Sequence of Events Chart')
    ax[0].set_ylabel('Time (s)')
    ax[0].set_xlabel('Time (s)')
    try:
        for i1 in range(0,len(tripnames)):
            ax[0].text(triptimes[i1],0.5,tripnames[i1],bbox=dict(facecolor='white', alpha=0.5))
    except:
        pass
    #ax2=ax1.twinx()
    ax[1].scatter(ttime,ifault,marker='.',label='current (A)')
    handles, labels = ax[1].get_legend_handles_labels()
    ax[1].legend(handles, labels, loc=4)
    ax[1].set_ylabel('Current (A)')
    del ttime
    del ifault
    plt.savefig(foldername+chartname+'-SOE', dpi=None, facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format=None,
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=None)
    datafile.close()
    plt.close()
#==============================================================================
# ip=100
# TD=1
# CT=1
# fcurve=cl.curveload('Nmod0',ip,CT,TD,0.01,0,0)
# dcurve=cl.curveload('KFmod3',ip,CT,TD,0.01,0,0)
# fuse=cl.curveload('15k',1,1,1,1,0,0)
# fshot=2
# dshot=2
# pshot=-1
# pshot2=-1
# fdelay=250
# ddelay=500
# ifcurrent=375
# 
# coordination(ip,fuse,fcurve,dcurve,fshot,dshot,pshot,pshot2,fdelay,ddelay,ifcurrent)
#==============================================================================


