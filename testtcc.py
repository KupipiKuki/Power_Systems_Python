# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 09:46:06 2019

@author: user
"""
#import powercad as pc
from pc_classes import curvegenerator as cg

testnumber=1

testdb={0 : ['tccTest',1,1200,'1200A Max Fault',1,300,'300A Min Fault',1,450,'450A Coord Fault'],
        1 : ['TimeAdderTest',1,7000,'7000A Max Fault',0,1200,'1200A Min Fault',1,5000,'5000A Coord Fault'],
        2 : ['LowCurrentCutoffTest',1,7000,'7000A Max Fault',0,1200,'1200A Min Fault',1,5000,'5000A Coord Fault'],
        3 : ['HighCurrentCutoffTest',1,7000,'7000A Max Fault',0,1200,'1200A Min Fault',1,5000,'5000A Coord Fault'],
        4 : ['MinMeltTotalClearTest',1,7000,'7000A Max Fault',0,1200,'1200A Min Fault',1,5000,'5000A Coord Fault'],
        5 : ['InstDelayTest',1,7000,'7000A Max Fault',0,1200,'1200A Min Fault',1,5000,'5000A Coord Fault']}

t=testdb[testnumber]
projectdir='./tccTests/'+t[0]+'/'

fcc=cg.curve_generator(projectdir,t[0])
fcc.Add_Fault(0,t[1],t[2],t[3])
fcc.Add_Fault(1,t[4],t[5],t[6])
fcc.Add_Fault(2,t[7],t[8],t[9])
fcc.Plot_Chart()