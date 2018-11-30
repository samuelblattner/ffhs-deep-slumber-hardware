import sys

import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
HIGH = True
LOW = False

print(0x10)

def readAnalogData(adcChannel, SCLKPin, MOSIPin, MISOPin, CSPin):

    GPIO.output(CSPin, HIGH)
    GPIO.output(CSPin, LOW)
    GPIO.output(SCLKPin, LOW)

    sendcmd = adcChannel
    sendcmd |= 0b00011000

    # Senden der Bitkombination

    for i in range(5):
        if sendcmd & 0x10:
            GPIO.output(MOSIPin, HIGH)
        else:
            GPIO.output(MOSIPin, LOW)

        # Negative Flanke des Clocksignals generieren
        GPIO.output(SCLKPin, HIGH)
        GPIO.output(SCLKPin, LOW)

        sendcmd <<= 1

    adcvalue = 0
    for i in range(11):
        GPIO.output(SCLKPin, HIGH)
        GPIO.output(SCLKPin, LOW)
        adcvalue <<= 1
        if GPIO.input(MISOPin):
            adcvalue |= 0x01
    time.sleep(0.5)
    return adcvalue


ADC_CHANNEL = 0
SCLK = 18
MOSI = 24
MISO = 23
CS = 25

GPIO.setup(SCLK, GPIO.OUT)
GPIO.setup(MOSI, GPIO.OUT)
GPIO.setup(MISO, GPIO.IN)
GPIO.setup(CS, GPIO.OUT)

print()
print()
print('A/D, Volts:')
while True:
    val = readAnalogData(ADC_CHANNEL, SCLK, MOSI, MISO, CS)
    sys.stdout.write('\r{}, {}v'.format(val, 3.3 * (val + 1) / 1024))
    sys.stdout.flush()

print('bye')
GPIO.cleanup()