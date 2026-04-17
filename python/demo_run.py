from libBeeS import BeeS
import time
m = BeeS()
# time.sleep(1)
for axis in range(16):
    m.setPowerOn(axis)
    m.setAccTime(axis, 200) 
    m.setTargetVelocity(axis, 2000)
    # m.setHomingLevel(axis, 0)
time.sleep(1)
m.setStateInit()
time.sleep(3)

# 依次从0到51200 再依次从51200到0
# read positions from positions.csv
# use numpy to load positions
import numpy as np
positions = np.loadtxt("positions.csv", delimiter=",", dtype=int)
print(positions)
offset = positions.tolist()
m.setTps(offset)
time.sleep(1)
m.setStateRun()
time.sleep(1)

tp = offset.copy()
time.sleep(2)
for loop in range(3):
    time.sleep(1)
    for axis in range(16):
        tp[axis] = 51200+offset[axis]
        m.setTps(tp)
        time.sleep(0.1)
    time.sleep(1)
    for axis in range(15,-1,-1):
        tp[axis] = 0+offset[axis]
        m.setTps(tp)
        time.sleep(0.1)
    
    

# for axis in range(8):
#     m.setPowerOff(axis)
# m.setStateInit()
time.sleep(1)
m.setPowerOff(0)
m.setStateInit()
time.sleep(1)
m.setStateRun()
tp = offset.copy()
while True:
    ap = m.getActualPosition(0)-offset[0]
    for axis in range(1,16):
        tp[axis] = ap+offset[axis]
    m.setTps(tp[1:16], start_id=1)


