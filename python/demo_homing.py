from libBeeS import BeeS
import time
m = BeeS()
for axis in range(16):
    m.setTargetVelocity(axis, 200)
    m.setHomingLevel(axis, 0)
    m.setHomingDir(axis, 1)
    m.setHomingMode(axis)
time.sleep(1)
m.setStateHoming()
time.sleep(1)

for axis in range(16):
    while not m.getReady(axis):
        time.sleep(0.1)
    print("axis {} ready".format(axis))
