import numpy as np
import scipy as sp
from math import pi
from math import sqrt
from math import atan2
import cmath as cm
import functions.constantvals as cval

#delta=np.array([cm.rect(42.5,-99.7*pi/180),
#              cm.rect(46.2,135.3*pi/180),
#              cm.rect(40.9,13.7*pi/180)])
#
#wye=np.array([(delta[0]-delta[1])*69/(24.9*sqrt(3)),
#              (delta[1]-delta[2])*69/(24.9*sqrt(3)),
#              (delta[2]-delta[0])*69/(24.9*sqrt(3))])
#
#wyep=np.array([((abs(wye[0])),atan2(wye[0].imag, wye[0].real)*180/pi),
#              ((abs(wye[1])),atan2(wye[1].imag, wye[1].real)*180/pi),
#              ((abs(wye[2])),atan2(wye[2].imag, wye[2].real)*180/pi)])
#print('IA: {:.2f} {:.2f}° IB: {:.2f} {:.2f}° IC: {:.2f} {:.2f}°'.format(wyep[0,0],wyep[0,1],wyep[1,0],wyep[1,1],wyep[2,0],wyep[2,1]))


sb=100.0e6
vb=np.array([69.0e3,
             24.9e3])
ib=np.array([sb/(vb[0]*np.sqrt(3)),
             sb/(vb[1]*np.sqrt(3))])
            
delta=np.array([[cm.rect(42.5,-99.7*pi/180)],
              [cm.rect(46.2,135.3*pi/180)],
              [cm.rect(40.9,13.7*pi/180)]])
#delta=np.array([[cm.rect(ib[0],0*pi/180)],
#              [cm.rect(ib[0],-120*pi/180)],
#              [cm.rect(ib[0],120*pi/180)]])

def dy1(ID):
    I012=sp.dot(cval.Ainv,ID)
    I012Y=np.multiply(cval.compy,I012)
    IY=sp.dot(cval.Amat,I012Y)   
    IYp=np.array([[abs(IY[0,0]),atan2(IY[0].imag, IY[0].real)*180/pi],
                  [abs(IY[1,0]),atan2(IY[1].imag, IY[1].real)*180/pi],
                  [abs(IY[2,0]),atan2(IY[2].imag, IY[2].real)*180/pi]])         
    print('IA: {:.2f} {:.2f}° IB: {:.2f} {:.2f}° IC: {:.2f} {:.2f}°'.format(IYp[0,0],IYp[0,1],IYp[1,0],IYp[1,1],IYp[2,0],IYp[2,1]))
    return IY

def yd1(IY):
    I012=sp.dot(cval.Ainv,IY)
    I012D=np.multiply(cval.compd,I012)
    ID=sp.dot(cval.Amat,I012D)
    IDp=np.array([[abs(ID[0,0]),atan2(ID[0].imag, ID[0].real)*180/pi],
                  [abs(ID[1,0]),atan2(ID[1].imag, ID[1].real)*180/pi],
                  [abs(ID[2,0]),atan2(ID[2].imag, ID[2].real)*180/pi]])
    print('IA: {:.2f} {:.2f}° IB: {:.2f} {:.2f}° IC: {:.2f} {:.2f}°'.format(IDp[0,0],IDp[0,1],IDp[1,0],IDp[1,1],IDp[2,0],IDp[2,1]))
    return ID

ID=np.array([[cm.rect(1,0*pi/180)],
             [cm.rect(1,-120*pi/180)],
             [cm.rect(1,120*pi/180)]])
IY=dy1(ID)
ID=yd1(IY)