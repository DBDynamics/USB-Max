from libBeeS import BeeS
import time

m = BeeS()
m.setStateAutoId()
time.sleep(1)
try:
    print("Auto ID mode. Press Ctrl+C to stop and scan devices...")
    num_prev = 0
    while True:
        num = m.getOnline()
        if num != num_prev:
            num_prev = num
            print("Online status changed:", num)
            #播放声音 数字num
            m.playSound(num)
        
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nCtrl+C detected. Switching to Ready state and scanning devices...")
    m.setStateReady()
    time.sleep(1)
    l = m.scanDevices()
    print("Scanned devices:", l)
