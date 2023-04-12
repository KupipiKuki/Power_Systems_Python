# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 09:46:06 2019

@author: user
"""
import powercad as pcd

projectname='temptest2'
projectdir='./'+projectname+'/'
fcc=pcd.faultCalculationClass()
fcc.calcImpedanceLaunch(projectdir,projectname,60,3)
print(fcc.xfmr(150,8,False,'rand',1))