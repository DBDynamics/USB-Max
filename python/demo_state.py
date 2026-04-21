import time
from libBeeS import BeeS

def main():
    m = BeeS()
    time.sleep(1)
    # m.setPowerOff(0)
    # m.setPowerOn(0)
    m.getEnable(0)
    print(m.getEnable(0))



if __name__ == "__main__":
    main()

