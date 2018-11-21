# -*- coding: utf-8 -*-
#Written by: Jason Cheers


import os
import functions.loads as ld

datafile=open('./System/SystemLoads.txt', 'w+')

datafile.write('*****************************************\n')
datafile.write('35 Member Load Estimations\n')
datafile.write('*****************************************\n')
resload=ld.mxresWG(30,3,2)
current=resload/14.4
datafile.write('Winter Gas: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')
resload=ld.mxresWG(15,2,1)
resload+=ld.mxresWE(15,1,1)
current=resload/14.4
datafile.write('\nWinter Gas\Electric: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')
resload=ld.mxres(30,3,2)
current=resload/14.4
datafile.write('\nSummer: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')

datafile.write('\n*****************************************\n')
datafile.write('50 Member Load Estimations\n')
datafile.write('*****************************************\n')
resload=ld.mxresWG(42,5,3)
current=resload/14.4
datafile.write('\nWinter Gas: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')
resload=ld.mxresWG(21,3,2)
resload+=ld.mxresWE(21,2,1)
current=resload/14.4
datafile.write('\nWinter Gas\Electric: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')
resload=ld.mxres(42,5,3)
current=resload/14.4
datafile.write('\nSummer: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')

datafile.write('\n*****************************************\n')
datafile.write('75 Member Load Estimations\n')
datafile.write('*****************************************\n')
resload=ld.mxresWG(65,7,3)
current=resload/14.4
datafile.write('\nWinter Gas: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')
resload=ld.mxresWG(33,4,2)
resload+=ld.mxresWE(32,3,1)
current=resload/14.4
datafile.write('\nWinter Gas\Electric: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')
resload=ld.mxres(65,7,3)
current=resload/14.4
datafile.write('\nSummer: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')

datafile.write('\n*****************************************\n')
datafile.write('100 Member Load Estimations\n')
datafile.write('*****************************************\n')
resload=ld.mxresWG(85,10,5)
current=resload/14.4
datafile.write('\nWinter Gas: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')
resload=ld.mxresWG(43,5,3)
resload+=ld.mxresWE(42,5,2)
current=resload/14.4
datafile.write('\nWinter Gas\Electric: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')
resload=ld.mxres(85,10,5)
current=resload/14.4
datafile.write('\nSummer: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')

datafile.write('\n*****************************************\n')
datafile.write('1000 Member Load Estimations\n')
datafile.write('*****************************************\n')
resload=ld.mxresWG(900,75,25)
current=resload/14.4
datafile.write('\nWinter Gas: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')
resload=ld.mxresWG(450,38,13)
resload+=ld.mxresWE(450,37,12)
current=resload/14.4
datafile.write('\nWinter Gas\Electric: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')
resload=ld.mxres(900,75,25)
current=resload/14.4
datafile.write('\nSummer: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')

datafile.write('\n*****************************************\n')
datafile.write('System Load Estimations\n')
datafile.write('*****************************************\n')
resload=ld.mxresWG(16500,2000,1000)
resload+=ld.mxresWE(16500,2000,1000)
resload+=ld.mxcomWG(950,48,2)
current=resload/14.4
datafile.write('Winter Gas\Electric: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')
resload=ld.mxres(33000,4000,2000)
resload+=ld.mxcom(950,48,2)
current=resload/14.4
datafile.write('Summer System: '+'%.2f' % resload + 'KW '+'%.2f' % current + 'A\n')
datafile.close()