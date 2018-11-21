# -*- coding: utf-8 -*-
#Written by: Jason Cheers


import os
import functions.loads as ld
import numpy as np


resloadmat=np.array([ld.mxres(53,50,50)])
for il in range(0,99):
    resload=ld.mxres(53,50,50)
    resloadmat=np.vstack((resloadmat,resload))

resload=np.sum((resloadmat))/100
current=resload/14.4
trip=current*1.5
print('Maricopa Dr: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A'+' Min Trip: %.2f' % trip + 'A')

resloadmat=np.array([ld.mxres(25,25,23)])
for il in range(0,99):
    resload=ld.mxres(25,25,23)
    resloadmat=np.vstack((resloadmat,resload))

resload=np.sum((resloadmat))/100
current=resload/14.4
trip=current*1.5
print('Lakeside Dr: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A'+' Min Trip: %.2f' % trip + 'A')

resloadmat=np.array([ld.mxres(50,50,50)])
for il in range(0,99):
    resload=ld.mxres(50,50,50)
    resloadmat=np.vstack((resloadmat,resload))

resload=np.sum((resloadmat))/100
current=resload/14.4
trip=current*1.5
print('Clearwater Dr A: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A'+' Min Trip: %.2f' % trip + 'A')

resloadmat=np.array([ld.mxres(69,60,60)])
for il in range(0,99):
    resload=ld.mxres(69,60,60)
    resloadmat=np.vstack((resloadmat,resload))

resload=np.sum((resloadmat))/100
current=resload/14.4
trip=current*1.5
print('Clearwater Dr B: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A'+' Min Trip: %.2f' % trip + 'A')
