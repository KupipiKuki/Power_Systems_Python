# -*- coding: utf-8 -*-
"""
14.4kV (V-family) pole loading example.

Assemblies are resolved from the RUS/In-House construction tables in
pc_classes/pc_data/Construction/14400_*.csv.
"""
from pc_classes.polecad import PoleCalcConfig, poleCalculationClass
from pc_classes.pc_functions import dataconstants as dct

projectname='Test14400'
projectdir='./PoleCadTests/'+projectname+'/'

config=PoleCalcConfig(
    project_name=projectname,
    project_dir=projectdir,
    design_tension=0.5,
    strength_factor=0.65,
    wind_load=4,
    wind_overload=2.5,
    tension_overload=1.65,
    ice_thickness=0.5,
    wind_angle=dct.northwind,
    deflection_factor=1,
    voltage_family='14400')

pcc=poleCalculationClass(config)
pcc.run()
