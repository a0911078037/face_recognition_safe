import time
import board
import adafruit_adxl34x
import os
i2c = board.I2C() 


accelerometer = adafruit_adxl34x.ADXL345(i2c)
count=0

accelerometer.enable_motion_detection()
while True:
    if accelerometer.events["motion"]:
        time.sleep(0.05)
        count+=1
    else:
        count=0
    if count>=3:
        os.system('aplay -Dhw:0,0 voice.mp3')
        count=0