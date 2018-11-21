# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 09:37:56 2014

@author: jcheers
"""

import matplotlib.pyplot as plt
import numpy as np
#Fuse
def fuseplot(offset):
    yd=np.array([])
    xd=np.array([])
    startln=np.array([[offset,0],[offset+0.5,0]])
    for i1 in range(0,1000):
        yd=np.append(yd,0.5*np.sin(i1/1000.0*np.pi*2))
        xd=np.append(xd,offset+1+(i1-500)/1000.0)
    endln=np.array([[offset+1.5,0],[offset+2,0]])
    return startln,xd,yd,endln

#Sectionalizer
def sectionalizerplot(offset):
    yd=np.array([])
    xd=np.array([])
    startln=np.array([[offset,0],[offset+0.5,0]])
    for i1 in range(0,1000):
        yd=np.append(yd,0.5*np.sin(i1/1000.0*np.pi*2))
        xd=np.append(xd,offset+1+(i1-500)/1000.0)
    endln=np.array([[offset+1.5,0],[offset+2,0]])
    slashln=np.array([[offset+0.5,-0.5],[offset+1.5,0.5]])
    return startln,xd,yd,endln,slashln

#Recloser
def recloserplot(offset):
    yd=np.array([])
    xd=np.array([])
    startln=np.array([[offset,0],[offset+0.5,0]])
    for i1 in range(0,1000):
        yd=np.append(yd,0.5*np.sin(i1/1000.0*np.pi*2))
        xd=np.append(xd,offset+1+0.5*np.cos(i1/1000.0*np.pi*2))
    endln=np.array([[offset+1.5,0],[offset+2,0]])
    slashln=np.array([[offset+1+0.5*np.cos(np.pi/4),0.5*np.sin(np.pi/4)],[offset+1+0.5*np.cos(5*np.pi/4),0.5*np.sin(5*np.pi/4)]])
    return startln,xd,yd,endln,slashln

def oneliner(devicetype,devicemat,foldername,plottitle):
    fig = plt.figure()
    ax=fig.add_subplot(111, aspect='equal')
    offset=0
    plotfontsize=10
    for linenum in range(0,len(devicetype)):
        if devicetype[linenum]==1:
            startln,xd,yd,endln,slashln=recloserplot(offset)
            ax.plot(startln[:,0],startln[:,1],color='black')
            ax.plot(xd,yd,color='black')
            ax.plot(endln[:,0],endln[:,1],color='black')
            ax.plot(slashln[:,0],slashln[:,1],color='black')
            ax.text(offset+1,0.8,devicemat[linenum,0], horizontalalignment='center',fontsize=plotfontsize)
            ax.text(offset+1,0.6,devicemat[linenum,1], horizontalalignment='center',fontsize=plotfontsize)
            ax.text(offset+1,-0.6,devicemat[linenum,2], horizontalalignment='center',verticalalignment='top',fontsize=plotfontsize)
            ax.text(offset+1,-0.8,devicemat[linenum,3], horizontalalignment='center',verticalalignment='top',fontsize=plotfontsize)
            offset+=2
            del startln,xd,yd,endln,slashln
        elif devicetype[linenum]==2:
            startln,xd,yd,endln=fuseplot(offset)
            ax.plot(startln[:,0],startln[:,1],color='black')
            ax.plot(xd,yd,color='black')
            ax.plot(endln[:,0],endln[:,1],color='black')
            ax.text(offset+1,0.8,devicemat[linenum,0], horizontalalignment='center',fontsize=plotfontsize)
            ax.text(offset+1,0.6,devicemat[linenum,1], horizontalalignment='center',fontsize=plotfontsize)
            ax.text(offset+1,-0.6,devicemat[linenum,2], horizontalalignment='center',verticalalignment='top',fontsize=plotfontsize)
            ax.text(offset+1,-0.8,devicemat[linenum,3], horizontalalignment='center',verticalalignment='top',fontsize=plotfontsize)
            offset+=2
            del startln,xd,yd,endln
        elif devicetype[linenum]==3:
            startln,xd,yd,endln,slashln=sectionalizerplot(offset)
            ax.plot(startln[:,0],startln[:,1],color='black')
            ax.plot(xd,yd,color='black')
            ax.plot(endln[:,0],endln[:,1],color='black')
            ax.plot(slashln[:,0],slashln[:,1],color='black')
            ax.text(offset+1,0.8,devicemat[linenum,0], horizontalalignment='center',fontsize=plotfontsize)
            ax.text(offset+1,0.6,devicemat[linenum,1], horizontalalignment='center',fontsize=plotfontsize)
            ax.text(offset+1,-0.6,devicemat[linenum,2], horizontalalignment='center',verticalalignment='top',fontsize=plotfontsize)
            ax.text(offset+1,-0.8,devicemat[linenum,3], horizontalalignment='center',verticalalignment='top',fontsize=plotfontsize)
            offset+=2
            del startln,xd,yd,endln,slashln
    plt.ylim(-1,1)
    ax.set_title(plottitle+' Single Line Diagram')
    plt.savefig(foldername+plottitle+'-SLD', dpi=None, facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format=None,
        transparent=False, bbox_inches=None, pad_inches=0.1,
        frameon=None)
    plt.close()

#devicetype=np.array([1,2,3])
#devicemat=np.array([['Recloser 1','100A','Nmod3 1 Shot','KFmod3 2 Shot'],
#                    ['Fuse 1',' ','25k',' '],
#                    ['Sectionalizer 1',' ','2 Shot',' ']])
#oneliner(devicetype,devicemat,'Scenario 1')