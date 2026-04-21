from libBeeS import BeeS
import time
m = BeeS()
m.setStateReady()
time.sleep(1)
l = m.scanDevices()
print(len(l), l)
