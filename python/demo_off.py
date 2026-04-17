from libBeeS import BeeS
import time

m = BeeS()
time.sleep(1)
for axis in range(16):
    m.setPowerOff(axis)
time.sleep(1)
m.setStateInit()
