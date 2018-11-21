# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 09:58:42 2013

@author: jcheers
Conductor Data
"""
import numpy as np

TOWERMAT=['VA1.1','VA1.2','VA1.3','VA2.1','VA1.1P','VA1.2P','VA1.3P',
          'VA2.1P','VA1.11','VA1.21','VA1.11P','VA1.21P','VB1.11','VB1.12',
          'VB1.13','VB1.11P','VB1.12P','VB1.13P','VB1.14','VB1.14P',
          'VC1.11','VC1.12','VC1.13','VC1.11P','VC1.12P','VC1.13P',
          'VC1.41','VC1.41L','VC1.41P','VC2.52','VC2.52L','C1-1NP',
          'C2NP','C1-41','VC2-VNP','VC2-VNPA','VC2-VNPB','VC2-VNPBR',
          'VC2-VNPR','TP-69','TP-69B','TP-69C','TP-69G','TP-69GB',
          'TP-69GC','TP-1','TP-2','TP-3','TP-4','TP-1A','TP-2A','TP-3A',
          'TP-4A','TPS-1','TS-1','TS-2','TS-1X','TS-2X','TS-1B','TS-1BX',
          'TS-1C','TS-1L','TS-1LX','TS-9','TSS-1','TSS-2','TSS-1B',
          'TSS-1C','TSS-1L','TSS-9','TSZ-1','TSZ-2','TU-1','TU-1A','TU-1AA',
          'TS-3','TS-3A','TS-4','TS-5','TS-5A','TS-3G','TS-3GA','TS-4G',
          'TS-5G','TS-5GA','TH-1','TH-1G','TH-1C','TH-1CX','TH-1CG',
          'TH-1CGX','TH-3','TH-4','TH-5','TH-3G','TH-4G','TH-5G','TH-5D',
          'TH-5GD','TH-7','TH-7G','TH-9','TH-9G','DBL3P','DBL3PUB']

VA11=np.array([[0,0,0],[48.3735464897913,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[1,1,0]])
VA11P=np.array([[0,0,0],[54.3323108288245,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[1,1,0]])
VA111=np.array([[0,0,0],[88.0227243386615,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[1,1,0]])
VA111P=np.array([[0,0,0],[88.2043082847998,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[1,1,0]])
VB111=np.array([[88,0,0],[59.9082632030006,50.3289181286465,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[2,1,0]])
VB111P=np.array([[88,0,0],[63.4113554499508,54.4518135602479,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[2,1,0]])
VB114=np.array([[88,0,0],[59.0338885725818,29.0688837074973,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[2,1,0]])
VB114P=np.array([[88,0,0],[59.3043000127309,29.6141857899217,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[2,1,0]])
VC111=np.array([[88,46.4865571966778,46.4865571966778],[59.9082632030006,50.3289181286465,48.3735464897913],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
VC111P=np.array([[88,46.4865571966778,46.4865571966778],[63.4113554499508,54.4518135602479,54.3323108288245],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
VC141=np.array([[37,75,112],[75.0266619276108,38.0525951808809,37.0540146272978],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
VC141L=np.array([[33,71,104],[71.028163428319,38.0525951808809,33.0605505096331],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
VC141P=np.array([[37,75,112],[75.4254598925323,38.8329756778952,37.8549864614954],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
VC252=np.array([[37,75,112],[82.2192191643779,59.5063021872474,73.5934779718964],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
VC252L=np.array([[37,71,108],[82.2192191643779,59.5063021872474,70.9365914038728],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
C11NP=np.array([[40,49.2442890089805,49.2442890089805],[114.004385880544,111.879399354841,156.115341975092],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
C141=np.array([[36,76,112],[76.4198926981712,40.7921561087423,36.8781778291715],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
C2VNP=np.array([[48,48,96],[145.120639469374,97.6729235765982,51.2640224719052],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
C2VNPA=np.array([[67.8822509939086,67.8822509939086,96],[147.091808065575,97.6729235765982,56.6038867923396],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
C2VNPB=np.array([[53.665631459995,53.665631459995,48],[147.091808065575,121.34249049694,100.578327685441],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
C2VNPBR=np.array([[56.6038867923396,56.6038867923396,60],[117.881296226331,85.9069263796581,61.773780845922],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
C2VNPR=np.array([[60,60,120],[180.897761180176,240.674053441579,300.539514872837],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TP69=np.array([[75.8946638440411,76.8374908491942,134.164078649987],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,0,0]])
TP69BC=np.array([[72,72,144],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,0,0]])
TP69G=np.array([[86.5332306111357,86.5332306111357,144],[75.8946638440411,145.986300727157,217.329243315298],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TP69GB=np.array([[72,72,144],[87.3613186713662,157.835357255591,229.259678094514],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TP1234=np.array([[84,55.9732078766261,55.9732078766261],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,0,0]])
TP1234A=np.array([[108,65.4599113962126,65.4599113962126],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,0,0]])
TPS1=np.array([[110.145358504115,108,110.145358504115],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,0,0]])
TS12=np.array([[120,108,72.9931503635786],[59.39696961967,126.142776249772,126.142776249772],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TS12X=np.array([[127.561749752816,108,84.8528137423857],[59.39696961967,137.08391590555,137.08391590555],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TS1B=np.array([[120,108,72.9931503635786],[91.2414379544733,162.24980739588,162.24980739588],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TS1BXC=np.array([[127.561749752816,108,84.8528137423857],[80.7774721070176,162.24980739588,162.24980739588],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TS1L=np.array([[136.821051011897,108,84],[61.773780845922,126.142776249772,126.142776249772],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TS1LX=np.array([[136.821051011897,108,84],[68.4105255059483,137.08391590555,137.08391590555],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TS9=np.array([[136.821051011897,108,84],[72.2495674727538,142.618371888057,142.618371888057],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TSS12=np.array([[137.411789887185,132,83.6779540858881],[63.6396103067893,142.239235093556,142.239235093556],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TSS1BC=np.array([[137.411789887185,132,83.6779540858881],[84.9058301885094,166.628328923986,166.628328923986],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TSS1L=np.array([[144.779142144164,132,81.8840643837371],[70.2922470831599,142.239235093556,142.239235093556],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TSS9=np.array([[144.779142144164,132,81.8840643837371],[74.2765104188397,147.580486514986,147.580486514986],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TSZ12=np.array([[118.11964273566,148.705245368144,97.9846926820715],[119.189974410602,153.388395910512,215.785194116742],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TU1=np.array([[115.879247494968,127.137720602503,84.8528137423857],[101.118742080783,144.086779407411,183.109257002479],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TU1A=np.array([[136.821051011897,120,84.8528137423857],[101.118742080783,183.109257002479,183.109257002479],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TU1AA=np.array([[84.8528137423857,84.8528137423857,168],[101.118742080783,183.109257002479,261.444066675838],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TS345A=np.array([[84,84,168],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,0,0]])
TS345AG=np.array([[84,84,168],[84,168,252],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,1,0]])
TH1=np.array([[126,126,252],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,0,0]])
TH1G=np.array([[126,126,252],[130.249760076554,130.249760076554,220.719278722997],[220.719278722997,130.249760076554,130.249760076554],[0,0,0],[126,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,2,0]])
TH1CX=np.array([[126,126,252],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,0,0]])
TH1CGX=np.array([[126,126,252],[151.700362557246,151.700362557246,234.019229979077],[234.019229979077,151.700362557246,151.700362557246],[0,0,0],[126,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,2,0]])
TH345=np.array([[144,144,288],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,0,0]])
TH34G=np.array([[144,144,288],[157.835357255591,229.259678094514,348.826604489967],[229.993478168404,157.990506043876,196.206523846686],[0,0,0],[193,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,2,0]])
TH5G=np.array([[144,144,288],[168.240898713719,259.200694443514,384.105454270048],[273.790065561189,175.775424903483,168.240898713719],[0,0,0],[288,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,2,0]])
THD=np.array([[126,126,252],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,0,0]])
TH5GD=np.array([[126,126,252],[157.178242769157,237.606818083994,346.353865288089],[237.606818083994,157.178242769157,157.178242769157],[0,0,0],[252,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,2,0]])
TH7=np.array([[126,126,252],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,0,0]])
TH7G=np.array([[126,126,252],[146.263460918987,146.263460918987,230.531993441258],[230.531993441258,146.263460918987,146.263460918987],[0,0,0],[126,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,2,0]])
TH9=np.array([[126,126,252],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,0,0]])
TH9G=np.array([[126,126,252],[130.249760076554,130.249760076554,220.719278722997],[220.719278722997,130.249760076554,130.249760076554],[0,0,0],[126,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[3,2,0]])
DBL3P=np.array([[72,64.621977685614,134.164078649987],[72,144,205.406913223484],[86.5332306111357,151.789327688082,216.333076527839],[0,0,0],[48,0,0],[72,64.621977685614,134.164078649987],[86.5332306111357,151.789327688082,216.333076527839],[72,144,205.406913223484],[0,0,0],[48,86.5332306111357,150.3595690337],[86.5332306111357,48,93.7229961108798],[150.3595690337,93.7229961108798,96],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[6,2,0]])
DBL3PUB=np.array([[72,64.621977685614,134.164078649987],[72,144,205.406913223484],[86.5332306111357,151.789327688082,216.333076527839],[398.898483326272,327.536257534948,273.642102023793],[48,468,470.455098813904],[72,64.621977685614,134.164078649987],[86.5332306111357,151.789327688082,216.333076527839],[72,144,205.406913223484],[396,324,265.088664412494],[48,86.5332306111357,150.3595690337],[86.5332306111357,48,93.7229961108798],[150.3595690337,93.7229961108798,96],[72,72,144],[268.328157299975,339.411254969543,410.813826446969],[264,336,408],[204,132,60],[197.909070029648,129.243955371228,93.7229961108798],[268.328157299975,197.909070029648,150.3595690337],[339.411254969543,268.328157299975,216.333076527839],[192,120,64.621977685614],[264,192,134.164078649987],[336,264,205.406913223484],[9,2,1]])