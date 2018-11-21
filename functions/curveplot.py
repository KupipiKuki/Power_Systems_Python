# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 11:04:49 2014

@author: jcheers
"""

import matplotlib.pyplot as plt

def plot6curves(curve1,curve2,curve3,curve4,curve5,curve6,curvenames,showifault,ifault,ifaultname,foldername,filename):
    fig = plt.figure()
    ax=fig.add_subplot(111, aspect='equal')
    ax.loglog(curve1[:,0], curve1[:,1],label=curvenames[0])
    ax.loglog(curve2[:,0], curve2[:,1],label=curvenames[1])
    ax.loglog(curve3[:,0], curve3[:,1],label=curvenames[2])
    ax.loglog(curve4[:,0], curve4[:,1],label=curvenames[3])
    ax.loglog(curve5[:,0], curve5[:,1],label=curvenames[4])
    ax.loglog(curve6[:,0], curve6[:,1],label=curvenames[5])
    if showifault:
        ax.loglog([ifault,ifault], [0.01,100],label=ifaultname)
    plt.xlim(10,100000)
    plt.ylim(0.01,100)
    plt.grid
    plt.grid(b=True, which='both', color='0.65',linestyle='-')
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc=1)
    ax.set_title(filename+' Time Coordination Chart')
    ax.set_xlabel('Current (A)')
    ax.set_ylabel('Time (s)')
    plt.savefig(foldername+filename+'-TCC', dpi=None, facecolor='w', edgecolor='w',
            orientation='portrait', papertype=None, format=None,
            transparent=False, bbox_inches=None, pad_inches=0.1,
            frameon=None)
    plt.close()

def plot5curves(curve1,curve2,curve3,curve4,curve5,curvenames,showifault,ifault,ifaultname,foldername,filename):
    fig = plt.figure()
    ax=fig.add_subplot(111, aspect='equal')
    ax.loglog(curve1[:,0], curve1[:,1],label=curvenames[0])
    ax.loglog(curve2[:,0], curve2[:,1],label=curvenames[1])
    ax.loglog(curve3[:,0], curve3[:,1],label=curvenames[2])
    ax.loglog(curve4[:,0], curve4[:,1],label=curvenames[3])
    ax.loglog(curve5[:,0], curve5[:,1],label=curvenames[4])
    if showifault:
        ax.loglog([ifault,ifault], [0.01,100],label=ifaultname)
    plt.xlim(10,100000)
    plt.ylim(0.01,100)
    plt.grid
    plt.grid(b=True, which='both', color='0.65',linestyle='-')
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc=1)
    ax.set_title(filename+' Time Coordination Chart')
    ax.set_xlabel('Current (A)')
    ax.set_ylabel('Time (s)')
    plt.savefig(foldername+filename+'-TCC', dpi=None, facecolor='w', edgecolor='w',
            orientation='portrait', papertype=None, format=None,
            transparent=False, bbox_inches=None, pad_inches=0.1,
            frameon=None)
    plt.close()

def plot4curves(curve1,curve2,curve3,curve4,curvenames,showifault,ifault,ifaultname,foldername,filename):
    fig = plt.figure()
    ax=fig.add_subplot(111, aspect='equal')
    ax.loglog(curve1[:,0], curve1[:,1],label=curvenames[0])
    ax.loglog(curve2[:,0], curve2[:,1],label=curvenames[1])
    ax.loglog(curve3[:,0], curve3[:,1],label=curvenames[2])
    ax.loglog(curve4[:,0], curve4[:,1],label=curvenames[3])
    if showifault:
        ax.loglog([ifault,ifault], [0.01,100],label=ifaultname)
    plt.xlim(10,100000)
    plt.ylim(0.01,100)
    plt.grid
    plt.grid(b=True, which='both', color='0.65',linestyle='-')
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc=1)
    ax.set_title(filename+' Time Coordination Chart')
    ax.set_xlabel('Current (A)')
    ax.set_ylabel('Time (s)')
    plt.savefig(foldername+filename+'-TCC', dpi=None, facecolor='w', edgecolor='w',
            orientation='portrait', papertype=None, format=None,
            transparent=False, bbox_inches=None, pad_inches=0.1,
            frameon=None)
    plt.close()

def plot3curves(curve1,curve2,curve3,curvenames,showifault,ifault,ifaultname,foldername,filename):
    fig = plt.figure()
    ax=fig.add_subplot(111, aspect='equal')
    ax.loglog(curve1[:,0], curve1[:,1],label=curvenames[0])
    ax.loglog(curve2[:,0], curve2[:,1],label=curvenames[1])
    ax.loglog(curve3[:,0], curve3[:,1],label=curvenames[2])
    if showifault:
        ax.loglog([ifault,ifault], [0.01,100],label=ifaultname)
    plt.xlim(10,100000)
    plt.ylim(0.01,100)
    plt.grid
    plt.grid(b=True, which='both', color='0.65',linestyle='-')
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc=1)
    ax.set_title(filename+' Time Coordination Chart')
    ax.set_xlabel('Current (A)')
    ax.set_ylabel('Time (s)')
    plt.savefig(foldername+filename+'-TCC', dpi=None, facecolor='w', edgecolor='w',
            orientation='portrait', papertype=None, format=None,
            transparent=False, bbox_inches=None, pad_inches=0.1,
            frameon=None)
    plt.close()

def plot2curves(curve1,curve2,curvenames,showifault,ifault,ifaultname,foldername,filename):
    fig = plt.figure()
    ax=fig.add_subplot(111, aspect='equal')
    ax.loglog(curve1[:,0], curve1[:,1],label=curvenames[0])
    ax.loglog(curve2[:,0], curve2[:,1],label=curvenames[1])
    if showifault:
        ax.loglog([ifault,ifault], [0.01,100],label=ifaultname)
    plt.xlim(10,100000)
    plt.ylim(0.01,100)
    plt.grid
    plt.grid(b=True, which='both', color='0.65',linestyle='-')
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc=1)
    ax.set_title(filename+' Time Coordination Chart')
    ax.set_xlabel('Current (A)')
    ax.set_ylabel('Time (s)')
    plt.savefig(foldername+filename+'-TCC', dpi=None, facecolor='w', edgecolor='w',
            orientation='portrait', papertype=None, format=None,
            transparent=False, bbox_inches=None, pad_inches=0.1,
            frameon=None)
    plt.close()