# -*- coding: utf-8 -*-
"""
Created on Wed Dec 30 09:50:42 2015

@author: jcheers
"""

from math import atan2
from math import pi

datafile.write('\n')
datafile.write('SLG Fault:\n')
datafile.write('Phase A: %.2f' % abs(Iabc[0,0])+'A %.2f'% (atan2(Iabc[0].imag, Iabc[0].real)*180/pi) + 'deg\n')
datafile.write('Ground: %.2f' % (abs(Iabc[12,0])*3)+'A %.2f'% (atan2(Iabc[12].imag, Iabc[12].real)*180/pi) + 'deg\n')
datafile.write('\n')
datafile.write('LL Fault:\n')
datafile.write('Phase A: %.2f' % abs(Iabc[3,0])+'A %.2f'% (atan2(Iabc[3].imag, Iabc[3].real)*180/pi) + 'deg\n')
datafile.write('Phase B: %.2f' % abs(Iabc[4,0])+'A %.2f'% (atan2(Iabc[4].imag, Iabc[4].real)*180/pi) + 'deg\n')
datafile.write('Phase C: %.2f' % abs(Iabc[5,0])+'A %.2f'% (atan2(Iabc[5].imag, Iabc[5].real)*180/pi) + 'deg\n')
datafile.write('Ground: %.2f' % (abs(Iabc[15,0])*3)+'A %.2f'% (atan2(Iabc[15].imag, Iabc[15].real)*180/pi) + 'deg\n')
datafile.write('\n')
datafile.write('LLG Fault:\n')
datafile.write('Phase A: %.2f' % abs(Iabc[6,0])+'A %.2f'% (atan2(Iabc[6].imag, Iabc[6].real)*180/pi) + 'deg\n')
datafile.write('Phase B: %.2f' % abs(Iabc[7,0])+'A %.2f'% (atan2(Iabc[7].imag, Iabc[7].real)*180/pi) + 'deg\n')
datafile.write('Phase C: %.2f' % abs(Iabc[8,0])+'A %.2f'% (atan2(Iabc[8].imag, Iabc[8].real)*180/pi) + 'deg\n')
datafile.write('Ground: %.2f' % (abs(Iabc[18,0])*3)+'A %.2f'% (atan2(Iabc[18].imag, Iabc[18].real)*180/pi) + 'deg\n')
datafile.write('\n')
datafile.write('3PH Fault:\n')
datafile.write('Phase A: %.2f' % abs(Iabc[9,0])+'A %.2f'% (atan2(Iabc[9].imag, Iabc[9].real)*180/pi) + 'deg\n')
datafile.write('Phase B: %.2f' % abs(Iabc[10,0])+'A %.2f'% (atan2(Iabc[10].imag, Iabc[10].real)*180/pi) + 'deg\n')
datafile.write('Phase C: %.2f' % abs(Iabc[11,0])+'A %.2f'% (atan2(Iabc[11].imag, Iabc[11].real)*180/pi) + 'deg\n')
datafile.write('Ground: %.2f' % (abs(Iabc[21,0])*3)+'A %.2f'% (atan2(Iabc[21].imag, Iabc[21].real)*180/pi) + 'deg\n')
datafile.write('\n')
datafile.write('******************************************************************************\n')
datafile.write('\n')