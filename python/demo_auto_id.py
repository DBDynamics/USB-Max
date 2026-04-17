from libBeeS import BeeS
import time

m = BeeS()
m.setStateAutoId()
time.sleep(1)
try:
    print("Auto ID mode. Press Ctrl+C to stop and scan devices...")
    while True:
        print("Online status:", m.getOnline())
        time.sleep(1)
except KeyboardInterrupt:
    print("\nCtrl+C detected. Switching to Ready state and scanning devices...")
    m.setStateReady()
    time.sleep(1)
    l = m.scanDevices()
    print("Scanned devices:", l)
