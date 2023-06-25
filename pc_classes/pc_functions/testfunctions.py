# -*- coding: utf-8 -*-
"""
Created on Fri Sep  2 07:52:27 2022

@author: jcheers
"""

import pandas as pd
import numpy as np
import numbers
import re

def testIsString(testval):
    if isinstance(testval, str):
        return True
    else:
        return False

def testIsEmptyString(testval):
    if testIsString(testval):
        if len(testval)>0:
            return False
        else:
            return True
    return False

def testIsNotEmptyString(testval):
    if testIsString(testval):
        if len(testval)>0:
            return True
    return False

def testIsNotNumber(testval):
    if (isinstance(testval, numbers.Real)==False) | (pd.isna(testval)):
        return True
    else:
        return False

def testIsNumber(testval):
    if (isinstance(testval, numbers.Real)==False) | (pd.isna(testval)):
        return False
    else:
        return True

def testIsZero(testval):
    try:
        if (testval==0.0):
            return True
        else:
            raise TypeError
    except TypeError:
        return False

def testPositiveFloat(testval):
    try:
        if (testval>0.0):
            return True
        else:
            raise TypeError
    except TypeError:
        return False

def testNegativeFloat(testval):
    try:
        if (testval<0.0):
            return True
        else:
            raise TypeError
    except TypeError:
        return False

def testAngleFloat(testval):
    try:
        if (testval>(-2*np.pi))&(testval<(2*np.pi)):
            return True
        else:
            raise TypeError
    except TypeError:
        return False

def remSpace(testval):
    return re.sub(r'[^\S\r\n]+','',testval)

#Make Windows Directory
def makeWinPath(oldPath):
    newPath = re.sub(r'/+',r'\\',oldPath)
    if not re.search(r'\\+$',newPath):
        newPath = re.sub(r'$',r'\\',newPath)
    return newPath

#Make Windows Directory
def makeWinPathFile(oldPath):
    newPath = re.sub(r'/+',r'\\',oldPath)
    return newPath

#Evaluates certain conditions as boolean true false
def boolEval(inVal=0):
    if type(inVal)==int:
        if inVal>0:
            retVal='True'
        else:
            retVal='False'
    elif type(inVal)==bool:
        if inVal==True:
            retVal='True'
        else:
            retVal='False'
    else:
        retVal='False'
    
    return retVal

#Evaluates certain conditions as boolean true false
def boolEvalPython(inVal=0):
    if isinstance(inVal, numbers.Real):
        if inVal>0:
            retVal=True
        else:
            retVal=False
    elif type(inVal)==str:
        if inVal in ['true','True','TRUE','1']:
            retVal=True
        else:
            retVal=False
    elif type(inVal)==bool:
        retVal=inVal
    else:
        retVal='False'
    
    return retVal

def stringBoolConvert(inVal=''):
    retVal=inVal
    if type(inVal)==str:
        if inVal=='True':
            retVal=True
        elif inVal=='False':
            retVal=False
    return retVal

def testIsAddress(testval):
    retMsg='OK'
    if type(testval) == str:
        if len(testval) >= 7 and len(testval) < 15:
            if not re.search(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',testval):
                retMsg='IP Address Invalid: ' + testval
        else:
            retMsg='IP Address Invalid: ' + testval
    else:
        retMsg='IP Address Invalid'
    
    return retMsg

#A function I resue all over multiple programs, seems to work well, modified with error message jcheers 2022
def testIsPointFormat(testval):
    retMsg='OK'
    if re.search(r'[^\S\r\n]+',testval):
        retMsg='Point contains invalid spaces'
    elif re.search(r'[!@#\$\^\&\*\)\(\+=\-\[\]<>\/%]+',testval):
        retMsg='Point contains invalid characters'
    elif re.search(r'[!@#\$\^\&\*\)\(\+=\-\[\]<>]+',testval):
        retMsg='Point contains invalid characters'
    elif re.search(r'_$',testval):
        retMsg='Point ends in an underscore'
    elif re.search(r'[^A-Za-z0-9_\.]+',testval):
        retMsg='Point contains invalid characters'
    elif re.search(r'_{2,}',testval):
        retMsg='Point contains consecutive underscores'
    if len(testval)<1:
        retMsg='Point name is too short'
    return retMsg

#Function I have used in extensions, works well jcheers 2022
def testIsNotNumberRange(testval, low, high):
    testState=0
    errMsg='OK'
    try:
        if type(testval)==int:
            testState=1
        elif type(testval)==float:
            testState=2
        elif type(testval)==str:
            if int(float(testval))==testval:
                testval=int(testval)
                testState=1
            else:
                #if its not a valid float the exception will trigger the default error string
                testval=float(testval)
                testState=2
        else:
            testState=0
    except:
        testState=0
    
    if testState==1:
        if (testval>=int(low)) & (testval<=int(high)):
           pass
        else:
            errMsg='Value out of range'
    elif testState==2:
        if (testval>=float(low)) & (testval<=float(high)):
           pass
        else:
            errMsg='Value out of range'
    else:
        errMsg='Value entered is not a valid number'
    return errMsg

#Function variant based on above for non decimal, works well jcheers 2022
def testIsNotIntRange(testval, low, high):
    testState=0
    errMsg='OK'
    try:
        if type(testval)==int:
            testState=1
        elif type(testval)==str:
            testval=int(testval)
            testState=1
        else:
            testState=0
    except:
        testState=0
    
    if testState==1:
        if (testval>=int(low)) & (testval<=int(high)):
           pass
        else:
            errMsg='Value out of range'
    else:
        errMsg='Value entered is not a valid integer'
    return errMsg