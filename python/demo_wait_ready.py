from libBeeS import BeeS
import time

m = BeeS()
m.setPowerOn(0)
m.setStateInit()
for loop in range(100):
    time.sleep(0.1)
    ret = m.getReady(0)
    print(ret)
