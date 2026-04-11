from libBeeS import BeeS
import time
m = BeeS()
# time.sleep(1)
for axis in range(8):
    m.setPowerOn(axis)
    m.setAccTime(axis, 200) 
    m.setTargetVelocity(axis, 2000)
    # m.setHomingLevel(axis, 0)
time.sleep(1)
m.setStateInit()
time.sleep(1)
m.setStateRun()
time.sleep(1)
for loop in range(100):
    m.setTp([0] * 8)
    time.sleep(1)
    m.setTp([51200] * 8)
    time.sleep(1)

# for axis in range(8):
#     m.setPowerOff(axis)
# m.setStateInit()
time.sleep(1)
