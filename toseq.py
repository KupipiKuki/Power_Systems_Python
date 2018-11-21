# -*- coding: utf-8 -*-
#Impedance Line Calculator, three phase complete
#Written by: Jason Cheers
#
#LineImpedanceCalc.py

import os
import numpy as np
import functions.PScalcs as ps
import functions.curveload as cl
import functions.curveplot as cplotter
import cmath as cm
from math import pi
from math import atan2

c1abc=np.array([[cm.rect(150,13*pi/180)],
              [cm.rect(120,-132*pi/180)],
              [cm.rect(110,114*pi/180)]])
c2abc=np.array([[cm.rect(46.6,0)],
              [cm.rect(25.3,2.52235)],
              [cm.rect(64.1,-2.11255)]])

seq=ps.abc2seq(c1abc)
c1zero=seq[0]*3

disp(seq)
#disp(abs(c1zero))
#disp(atan2(c1zero.imag, c1zero.real))
#c1zero=c1abc[0]+c1abc[1]+c1abc[2]
#disp(abs(c1zero))
#disp(atan2(c1zero.imag, c1zero.real))

seq=ps.abc2seq(c2abc)
c2zero=seq[0]*3

#disp(abs(c2zero))
#disp(atan2(c2zero.imag, c2zero.real))
#c2zero=c2abc[0]+c2abc[1]+c2abc[2]
#disp(abs(c2zero))
#disp(atan2(c2zero.imag, c2zero.real))