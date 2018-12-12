from RPi import GPIO
import time
from phue import Bridge

# b = Bridge('192.168.1.129')
# b.set_group(0, {'on': True, 'bri': 255}, transitiontime=50)

GPIO.setmode(GPIO.BCM)
GPIO.setup(20, GPIO.IN)

try:
    while True:
        if GPIO.input(20) == 0:
            # b.set_group(0, {'on': False}, transitiontime=25)
            print(0)
        else:
            # b.set_group(0, {'on': True, 'bri': 255}, transitiontime=50)
            print(1)
        time.sleep(1)

except KeyboardInterrupt:
    print('Goodbye')

GPIO.cleanup()
