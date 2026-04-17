from libBeeS import BeeS
import time

m = BeeS()
m.setCurrentID(1)
m.setTargetID(7)
time.sleep(1)
m.setStateManualID()
time.sleep(1)

