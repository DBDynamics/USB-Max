from libBeeS import BeeS
import time

m = BeeS()
time.sleep(1)

# 连续读取0-15轴的数据 (一次性USB通信)
positions = m.getAps(count=16, start_id=0)

for axis, pos in enumerate(positions):
    print(f"Axis {axis} position: {pos}")

print("\nAll positions (0-15):", positions)
# save positions to csv file
# use numpy to save positions
import numpy as np
np.savetxt("positions.csv", positions, delimiter=",")
print("Positions saved to positions.csv")
