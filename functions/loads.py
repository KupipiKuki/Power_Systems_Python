# -*- coding: utf-8 -*-
"""
Created on Wed Aug 28 14:41:27 2013

@author: jcheers
"""

import scipy.stats as ssp

def smres(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=4,scale=1)
    return load

def mdres(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=6,scale=1)
    return load

def lgres(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=8,scale=1)
    return load

def smresWE(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=3,scale=1)
    return load

def mdresWE(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=4,scale=1)
    return load

def lgresWE(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=5,scale=1)
    return load

def smresWG(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=0.5,scale=0.25)
    return load

def mdresWG(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=1.5,scale=0.75)
    return load

def lgresWG(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=3,scale=1)
    return load

def smcom(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=25,scale=4)
    return load

def mdcom(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=75,scale=10)
    return load

def lgcom(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=150,scale=25)
    return load

def smcomWG(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=15,scale=4)
    return load

def mdcomWG(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=60,scale=10)
    return load

def lgcomWG(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=120,scale=25)
    return load
    
def smind(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=100,scale=20)
    return load

def mdind(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=500,scale=100)
    return load

def lgind(num):
    load=0
    for i1 in range(0,num):
        load+=ssp.norm.rvs(loc=1000,scale=200)
    return load

def mxres(numsm,nummd,numlg):
    load=0
    load+=smres(numsm)
    load+=mdres(nummd)
    load+=lgres(numlg)
    return load

def mxresWG(numsm,nummd,numlg):
    load=0
    load+=smresWG(numsm)
    load+=mdresWG(nummd)
    load+=lgresWG(numlg)
    return load

def mxresWE(numsm,nummd,numlg):
    load=0
    load+=smresWE(numsm)
    load+=mdresWE(nummd)
    load+=lgresWE(numlg)
    return load
    
def mxcom(numsm,nummd,numlg):
    load=0
    load+=smcom(numsm)
    load+=mdcom(nummd)
    load+=lgcom(numlg)
    return load
    
def mxcomWG(numsm,nummd,numlg):
    load=0
    load+=smcomWG(numsm)
    load+=mdcomWG(nummd)
    load+=lgcomWG(numlg)
    return load
    
def mxind(numsm,nummd,numlg):
    load=0
    load+=smind(numsm)
    load+=mdind(nummd)
    load+=lgind(numlg)
    return load

#resload=mxres(35000,2600,1000)
#resload=mxres(35,25,13)
#current=resload/14.4
#print(' :'+'%.2f' % resload + 'KW '+'%.2f' % current + 'A')
#comload=mxcom(500,40,15)
#indload=mxind(50,40,5)
#totload=resload+comload+indload
#print(resload)
#print(comload)
#print(indload)
#print(totload)