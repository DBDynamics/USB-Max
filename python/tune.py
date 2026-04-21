from libBeeS import BeeS
import time

m = BeeS()

m.setCurrentID(0)
m.setKPP(1024)
m.setKPI(1)
m.setKPD(0)
m.setKFF(2048)
time.sleep(0.5)
m.setStateTune()
time.sleep(0.5)
