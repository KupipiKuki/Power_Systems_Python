# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 09:46:06 2019

@author: user
"""
from pc_classes import curvegenerator as cg
from coord import ocdevdb as oc
import pandas as pd

testnumber=18

inrush=[25000/14400,37500/14400,50000/14400,75000/14400,100000/14400,167000/14400,250000/14400,334000/14400,430000/14400,515000/14400,700000/14400,850000/14400,1100000/14400]

testdb={0 : ['coord',[[1,7000,'7000A Max Fault']]],
        1 : ['25kVA',[[1,inrush[0],'{:.2f}A Full Load - No Time Shown'.format(inrush[0]),False],[1,inrush[0]*3,'3x Inrush'],[1,inrush[0]*10,'10x Inrush'],[1,inrush[0]*25,'25x Inrush']]],
        2 : ['37.5kVA',[[1,inrush[1],'{:.2f}A Full Load - No Time Shown'.format(inrush[1]),False],[1,inrush[1]*3,'3x Inrush'],[1,inrush[1]*10,'10x Inrush'],[1,inrush[1]*25,'25x Inrush']]],
        3 : ['50kVA',[[1,inrush[2],'{:.2f}A Full Load - No Time Shown'.format(inrush[2]),False],[1,inrush[2]*3,'3x Inrush'],[1,inrush[2]*10,'10x Inrush'],[1,inrush[2]*25,'25x Inrush']]],
        4 : ['75kVA',[[1,inrush[3],'{:.2f}A Full Load - No Time Shown'.format(inrush[3]),False],[1,inrush[3]*3,'3x Inrush'],[1,inrush[3]*10,'10x Inrush'],[1,inrush[3]*25,'25x Inrush']]],
        5 : ['100kVA',[[1,inrush[4],'{:.2f}A Full Load - No Time Shown'.format(inrush[4]),False],[1,inrush[4]*3,'3x Inrush'],[1,inrush[4]*10,'10x Inrush'],[1,inrush[4]*25,'25x Inrush']]],
        6 : ['167kVA',[[1,inrush[5],'{:.2f}A Full Load - No Time Shown'.format(inrush[5]),False],[1,inrush[5]*3,'3x Inrush'],[1,inrush[5]*10,'10x Inrush'],[1,inrush[5]*25,'25x Inrush']]],
        7 : ['250kVA',[[1,inrush[6],'{:.2f}A Full Load - No Time Shown'.format(inrush[6]),False],[1,inrush[6]*3,'3x Inrush'],[1,inrush[6]*10,'10x Inrush'],[1,inrush[6]*25,'25x Inrush']]],
        8 : ['334kVA',[[1,inrush[7],'{:.2f}A Full Load - No Time Shown'.format(inrush[7]),False],[1,inrush[7]*3,'3x Inrush'],[1,inrush[7]*10,'10x Inrush'],[1,inrush[7]*25,'25x Inrush']]],
        9 : ['430kVA',[[1,inrush[8],'{:.2f}A Full Load - No Time Shown'.format(inrush[8]),False],[1,inrush[8]*3,'3x Inrush'],[1,inrush[8]*10,'10x Inrush'],[1,inrush[8]*25,'25x Inrush']]],
        10 : ['515kVA',[[1,inrush[9],'{:.2f}A Full Load - No Time Shown'.format(inrush[9]),False],[1,inrush[9]*3,'3x Inrush'],[1,inrush[9]*10,'10x Inrush'],[1,inrush[9]*25,'25x Inrush']]],
        11 : ['700kVA',[[1,inrush[10],'{:.2f}A Full Load - No Time Shown'.format(inrush[10]),False],[1,inrush[9]*3,'3x Inrush'],[1,inrush[10]*10,'10x Inrush'],[1,inrush[10]*25,'25x Inrush']]],
        12 : ['850kVA',[[1,inrush[11],'{:.2f}A Full Load - No Time Shown'.format(inrush[11]),False],[1,inrush[9]*3,'3x Inrush'],[1,inrush[11]*10,'10x Inrush'],[1,inrush[11]*25,'25x Inrush']]],
        13 : ['1100kVA',[[1,inrush[12],'{:.2f}A Full Load - No Time Shown'.format(inrush[12]),False],[1,inrush[9]*3,'3x Inrush'],[1,inrush[12]*10,'10x Inrush'],[1,inrush[12]*25,'25x Inrush']]],
        14 : ['10KS-3D',[[1,1000,'1000A Fault']]],
        15 : ['15KS-7D',[[1,1200,'1200A Fault']]],
        16 : ['15KS-10KS',[[1,1000,'1000A Fault']]],
        17 : ['20KS-10KS',[[1,1250,'1250A Fault']]],
        18 : ['25KS-10KS',[[1,1950,'1950A Fault']]]}


t=testdb[testnumber]
projectdir='./coord/'+t[0]+'/'

if testnumber in oc.ocddevdb_data.keys():
    fcc=cg.curve_generator(projectdir,t[0],ocdevdb=pd.DataFrame(oc.ocddevdb_data[testnumber],columns=oc.columns))
else:
    fcc=cg.curve_generator(projectdir,t[0])

for f in range(len(t[1])):
    if len(t[1][f])<4:
        fcc.Add_Fault(f,t[1][f][0],t[1][f][1],t[1][f][2])
    else:
        fcc.Add_Fault(f,t[1][f][0],t[1][f][1],t[1][f][2],t[1][f][3])

if testnumber > 0 and testnumber < 19:
    fcc.Plot_Chart(xlim=[1,10000])
else:
    fcc.Plot_Chart()
    
xfmrtest=cg.xfmr_damage_curve(139,6,2)