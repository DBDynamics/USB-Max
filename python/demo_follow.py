from libBeeS import BeeS
import time
import numpy as np

positions = np.loadtxt("positions.csv", delimiter=",", dtype=int)
offset = positions.tolist()

m = BeeS()
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
    # time.sleep(0.01)
