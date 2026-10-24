# -*- coding: utf-8 -*-
"""Impedance/ampacity study on the temptest2 project (refactored API)."""
from pc_classes.powercad import PowerCalcConfig, faultCalculationClass

projectname = 'temptest2'
projectdir = './PowerCadTests/' + projectname + '/'

config = PowerCalcConfig(
    project_name=projectname,
    project_dir=projectdir,
    frequency=60,
    environmenttype=3,
)
fcc = faultCalculationClass(config)
fcc.run()
print(fcc.xfmr(150, 8, False, 'rand', 1))
