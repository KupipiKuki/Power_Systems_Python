# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 07:46:14 2019

@author: jcheers
"""

import pandas as pd
import numpy as np
import numbers


def testIsString(testval):
    if isinstance(testval, str):
        return True
    else:
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