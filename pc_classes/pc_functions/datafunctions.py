# -*- coding: utf-8 -*-
"""
Created on Sun Jun 18 13:16:13 2023

@author: jmc53
"""

from pathlib import Path

import pandas as pd
import numpy as np
from cmath import rect

_DATA_DIR = Path(__file__).resolve().parent.parent / 'pc_data'

def generate_pole_data():

    wd=pd.ExcelFile(_DATA_DIR / 'PoleData' / 'WoodPoles.xlsx')

    for sh in range(0, len(wd.sheet_names)):
        shname=wd.sheet_names[sh]
        if sh==0:
            wooddata = pd.concat([wd.parse(shname)],keys=[shname],names=['Species','Number'])
        else:
            wooddata = pd.concat([wooddata,pd.concat([wd.parse(shname)],keys=[shname],names=['Species','Number'])])
    
    return wooddata

def generate_pole_construction():

    const = {'7200_A' : pd.read_csv(_DATA_DIR / 'Construction' / '7200_A.csv'),
             '7200_B' : pd.read_csv(_DATA_DIR / 'Construction' / '7200_B.csv'),
             '7200_C' : pd.read_csv(_DATA_DIR / 'Construction' / '7200_C.csv')}
    
    return const

def generate_conductor_database():

    acsr=pd.read_csv(_DATA_DIR / 'Conductors' / 'ACSR.csv',encoding='ISO-8859-1')
    aaac=pd.read_csv(_DATA_DIR / 'Conductors' / 'AAAC.csv')
    aac=pd.read_csv(_DATA_DIR / 'Conductors' / 'AAC.csv')
    copper=pd.read_csv(_DATA_DIR / 'Conductors' / 'COPPER.csv')
    copperweld=pd.read_csv(_DATA_DIR / 'Conductors' / 'COPPERWELD40.csv')
    copperweldcopper=pd.read_csv(_DATA_DIR / 'Conductors' / 'COPPERWELDCOPPER.csv')
    triplex=pd.read_csv(_DATA_DIR / 'Conductors' / 'TRIPLEX.csv')
    conductordb=pd.concat([acsr,aaac,aac,copper,copperweld,copperweldcopper,triplex],keys=['ACSR','AAAC','AAC','Copper','Copperweld','CopperweldCopper','Triplex'])

    return conductordb

def generate_cable_database():
    driliteOL=pd.read_csv(_DATA_DIR / 'Conductors' / 'DRILITE.csv')
    drilite6m=pd.read_csv(_DATA_DIR / 'Conductors' / 'DRILITE6M.csv')
    drilite10m=pd.read_csv(_DATA_DIR / 'Conductors' / 'DRILITE10M.csv')
    drilite16m=pd.read_csv(_DATA_DIR / 'Conductors' / 'DRILITE16M.csv')
    tel6m=pd.read_csv(_DATA_DIR / 'Conductors' / 'TEL6M.csv')
    tel10m=pd.read_csv(_DATA_DIR / 'Conductors' / 'TEL10M.csv')
    tel16m=pd.read_csv(_DATA_DIR / 'Conductors' / 'TEL16M.csv')
    telOL=pd.read_csv(_DATA_DIR / 'Conductors' / 'TELOL.csv')
    fortex6m=pd.read_csv(_DATA_DIR / 'Conductors' / 'FORTEX6M.csv')
    fortex10m=pd.read_csv(_DATA_DIR / 'Conductors' / 'FORTEX10M.csv')
    fortex16m=pd.read_csv(_DATA_DIR / 'Conductors' / 'FORTEX16M.csv')
    cabledb=pd.concat([driliteOL,drilite6m,drilite10m,drilite16m,tel6m,tel10m,tel16m,telOL,fortex6m,fortex10m,fortex16m],keys=['Drilite','Drilite6M','Drilite10M','Drilite16M','Tel6M','Tel10M','Tel16M','Tel0L','Fortex6M','Fortex10M','Fortex16M'])

    return cabledb

def generate_transforms():

    a = rect(1,(2*np.pi)/3)

    Amat = np.asmatrix([[1, 1, 1], [1, a**2, a], [1, a, a**2]])
    Ainv = (1.0/3.0)*np.asmatrix([[1, 1, 1], [1, a, a**2], [1, a**2, a]])
    
    #Add 30 degree phase shifts (could be simplified to 0,rect(1,np.pi/6),rect(1,-np.pi/6) and remove squre root )
    compd=(1/np.sqrt(3))*np.array([[0],[(1-a)],[(1-a**2)]])
    compy=(1/np.sqrt(3))*np.array([[0],[(1-a**2)],[(1-a)]])
    
    return Amat, Ainv, compd, compy
