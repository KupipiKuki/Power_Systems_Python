# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 16:07:07 2023

@author: jmc53
"""

import pandas as pd
import numpy as np
import cmath
from .pc_functions import datafunctions as dfn

class FaultCalculator():
    
    def __init__(self):

        self.Amat,self.Ainv,self.compd,self.compy=dfn.generate_transforms()
        
        a = cmath.rect(1,(2*np.pi)/3)

        Amat = np.mat([[1, 1, 1], [1, a**2, a], [1, a, a**2]])
        Ainv = (1.0/3.0)*np.mat([[1, 1, 1], [1, a, a**2], [1, a**2, a]])
        self.compd=(1/np.sqrt(3))*np.array([[0],[(1-a)],[(1-a**2)]])
        self.compy=(1/np.sqrt(3))*np.array([[0],[(1-a**2)],[(1-a)]])

    def ifault(self,zlt,vf,zgnd,zfault):
        """
        ifault\n
        \n
        zlt - impedance in pu, np.array complex format [[r1+x1j],[r0+x0j]]
        vf - voltage in pu, float
        zgnd - ground impedance in pu, float
        zfault - fault impedance in pu, float
        pandas columns:
            0 Iabc matrix
            1 Iabc matrix dy viewed from D
            2 Iabc matrix yd viewed from Y
            3 I012 matrix
            4 I012 matrix dy viewed from D
            5 I012 matrix yd viewed from Y
        """
        zt=zlt[0,0]
        z0t=zlt[1,0]
        #*********************************************************************#
        #Phase to Ground Fault, (A-G)
        #*********************************************************************#
        #Generate Phase Current Matrix From Sequence Current Matrix
        I012=np.array([[(vf/(z0t+zt+zt+zfault+(3*zgnd)))],
                       [(vf/(z0t+zt+zt+zfault+(3*zgnd)))],
                       [(vf/(z0t+zt+zt+zfault+(3*zgnd)))]])
        Iabc=np.dot(self.Amat,I012)
        Iseq=I012
        #Generate Results Moving Backwards from a low Wye to High Delta
        I012d=np.multiply(self.compy,I012)
        IabcD=np.dot(self.Amat,I012d)
        IseqD=I012d
        #Generate Results Moving Backwards from a low Delta to High Wye
        I012y=np.multiply(self.compd,Iseq)
        IabcY=np.dot(self.Amat,I012y)
        IseqY=I012y
        #*********************************************************************#
        #Phase to Phase Fault, (BC)
        #*********************************************************************#
        #Generate Phase Current Matrix From Sequence Current Matrix
        I012=np.array([[0],
        			   [(vf/(zt+zt+(zfault)))],
        			   [-vf/(zt+zt+(zfault))]])
        Iabc=np.vstack((Iabc,np.dot(self.Amat,I012)))
        Iseq=np.vstack((Iseq,I012))
        #Generate Results Moving Backwards from a low Wye to High Delta
        I012d=np.multiply(self.compy,I012)
        IabcD=np.vstack((IabcD,np.dot(self.Amat,I012d)))
        IseqD=np.vstack((IseqD,I012d))
        #Generate Results Moving Backwards from a low Delta to High Wye
        I012y=np.multiply(self.compd,I012)
        IabcY=np.vstack((IabcY,np.dot(self.Amat,I012y)))
        IseqY=np.vstack((IseqY,I012y))
        #*********************************************************************#
        #Phase to Phase to Ground Fault, (BC-G)
        #*********************************************************************#
        #Calculate Positive Sequence Impedance Equation
        #I1=vf/((zt+zfault)+(((zt+zfault)*(z0t+(3*zgnd)))/(zt+z0t+(3*zgnd))))
        I1=vf/(zt+(zfault/2)+((zt+(zfault/2))*(z0t+(zfault/2)+(3*zgnd)))/(zt+z0t+zfault+(3*zgnd)))
        #Generate Phase Current Matrix From Sequence Current Matrix
        #I012=np.array([[(-I1*((zt+zfault)/(zt+z0t+zfault+(3*zgnd))))],
        #			   [I1],
        #			   [(-I1*((z0t+zfault+(3*zgnd))/(zt+z0t+(2*zfault)+(3*zgnd))))]])
        I012=np.array([[-I1*(z0t/(zt+z0t))],
        			   [I1],
        			   [-I1*(zt/(zt+z0t))]])
        Iabc=np.vstack((Iabc,np.dot(self.Amat,I012)))
        Iseq=np.vstack((Iseq,I012))
        #Generate Results Moving Backwards from a low Wye to High Delta
        I012d=np.multiply(self.compy,I012)
        IabcD=np.vstack((IabcD,np.dot(self.Amat,I012d)))
        IseqD=np.vstack((IseqD,I012d))
        #Generate Results Moving Backwards from a low Delta to High Wye
        I012y=np.multiply(self.compd,I012)
        IabcY=np.vstack((IabcY,np.dot(self.Amat,I012y)))
        IseqY=np.vstack((IseqY,I012y))
        #*********************************************************************#
        #Three Phase to Ground Fault
        #*********************************************************************#
        #Calculate Positive Sequence Impedance Equation
        I1=(vf/(zt+zfault+zgnd))
        I012=np.array([[0],[I1],[0]])
        Iabc=np.vstack((Iabc,np.dot(self.Amat,I012)))
        Iseq=np.vstack((Iseq,I012))
        #Generate Results Moving Backwards from a low Wye to High Delta
        I012d=np.multiply(self.compy,I012)
        IabcD=np.vstack((IabcD,np.dot(self.Amat,I012d)))
        IseqD=np.vstack((IseqD,I012d))
        #Generate Results Moving Backwards from a low Delta to High Wye
        I012y=np.multiply(self.compd,I012)
        IabcY=np.vstack((IabcY,np.dot(self.Amat,I012y)))
        IseqY=np.vstack((IseqY,I012y))
        
# =============================================================================
#         if matreturn==1:
#             return IabcD
#         elif matreturn==2:
#             return IabcY
#         elif matreturn==3:
#             return IseqD
#         elif matreturn==4:
#             return IseqY
#         elif matreturn==5:
#             return Iseq
#         else:
#             return Iabc
# =============================================================================
        fault_df=pd.DataFrame(np.hstack((Iabc,IabcD,IabcY,Iseq,IseqD,IseqY)),
                              columns=['ABC','ABC dy1 D','ABC yd1 Y',
                                       '012','012 dy1 D','012 yd1 Y'])
        return fault_df

    def conv_fault(self,imat,itype=0):
        """
        ifault\n
        \n
        imat - numpy array single column, complex A,B,C
        itype, return pandas columns:
            0 Iabc matrix
            1 Iabc matrix dy viewed from D
            2 Iabc matrix yd viewed from Y
            3 I012 matrix
            4 I012 matrix dy viewed from D
            5 I012 matrix yd viewed from Y
        """
        
        if itype<1:
            Iabc=imat
            I012=np.dot(self.Ainv,Iabc)
            I012d=np.multiply(self.compy,I012)
            IabcD=np.dot(self.Amat,I012d)
            I012y=np.multiply(self.compd,I012)
            IabcY=np.dot(self.Amat,I012y)
        elif itype<2:
            IabcD=imat
            I012d=np.dot(self.Ainv,IabcD)
            #I012=np.multiply(np.array([[1],[cmath.rect(1,-np.pi/6)],[cmath.rect(1,np.pi/6)]]),I012d)
            #I012=np.multiply(self.compd,I012d)
            I012=np.multiply(np.array([[0],[1/cmath.rect(1,-np.pi/6)],[1/cmath.rect(1,np.pi/6)]]),I012d)
            #I012=np.multiply(self.compy,I012d)
            Iabc=np.dot(self.Amat,I012)
            
            #adj_mat=np.array([[1,0,0],[0,1,0],[0,0,1]])
            #ifcHS=(adj_mat*ifc[0:3])/np.sqrt(3)
            #Iabc=
            adj_mat=np.array([[1,0,-1],[-1,1,0],[0,-1,1]])*1/3
            #adj_mat=np.array([[1,-1,0],[0,1,-1],[-1,0,1]])
            # compute the pseudo inverse of A
            # computationally intensive for large problems
            #adj_mat = np.linalg.pinv(adj_mat)
            #print(adj_mat)
            #Iabc=np.dot(adj_mat,IabcD)
            adj_mat=np.array([[1,-1,0],[1,2,0],[-2,-1,0]])*1/3
            Iabc=np.dot(adj_mat*(1/(69/24.9/np.sqrt(3))),IabcD)
            I012y=np.multiply(self.compd,I012d)
            IabcY=np.dot(self.Amat,I012y)
        elif itype<3:
            IabcY=imat
            I012y=np.dot(self.Ainv,IabcY)
            I012=np.multiply(self.compd,I012d)
            Iabc=np.dot(self.Amat,I012)
            I012d=np.multiply(self.compy,I012)
            IabcD=np.dot(self.Amat,I012d)
        elif itype<4:
            I012=imat
            Iabc=np.dot(self.Amat,I012)
            I012d=np.multiply(self.compy,I012)
            IabcD=np.dot(self.Amat,I012d)
            I012y=np.multiply(self.compd,I012)
            IabcY=np.dot(self.Amat,I012y)
        elif itype<5:
            I012d=imat
            IabcD=np.dot(self.Amat,I012d)
            I012=np.multiply(self.compd,I012d)
            Iabc=np.dot(self.Amat,I012)
            I012y=np.multiply(self.compd,I012)
            IabcY=np.dot(self.Amat,I012y)
        else:
            I012y=imat
            IabcY=np.dot(self.Amat,I012y)
            I012=np.multiply(self.compy,I012y)
            Iabc=np.dot(self.Amat,I012)
            I012d=np.multiply(self.compy,I012)
            IabcD=np.dot(self.Amat,I012d)

        fault_df=pd.DataFrame(np.hstack((Iabc,IabcD,IabcY,I012,I012d,I012y)),
                              columns=['ABC','ABC dy1 D','ABC yd1 Y',
                                       '012','012 dy1 D','012 yd1 Y'])
        return fault_df