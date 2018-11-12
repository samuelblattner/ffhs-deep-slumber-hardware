from RPi import GPIO
import time
from phue import Bridge
from sense_hat import SenseHat

b = Bridge('192.168.1.129')
sense = SenseHat()
b.set_group(0, {'on': True, 'bri': 254}, transitiontime=50)

GPIO.setmode(GPIO.BCM)
GPIO.setup(16, GPIO.IN)

try:
    while True:
        if GPIO.input(16) == 0:
            b.set_group(0, {'on': False}, transitiontime=25)
        else:
            b.set_group(0, {'on': True, 'bri': 254}, transitiontime=50)
        time.sleep(1)

        print(sense.get_gyroscope_raw())

except KeyboardInterrupt:
    print('Goodbye')

GPIO.cleanup()