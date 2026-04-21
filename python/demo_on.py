from libBeeS import BeeS
import time

m = BeeS()
# m.setTp([51200] * 8)
for axis in range(16):
    m.setPowerOn(axis)
# m.setPowerOn(0)
m.setStateInit()
# print(m.getActualPosition(0))
# m.setStateRun()

time.sleep(1)