import requests
import time
import RPi.GPIO as GPIO

CONTROL_PIN = 17
PWM_FREQ = 50
STEP=15

'''
global variables
'''

GPIO.setmode(GPIO.BCM)
GPIO.setup(CONTROL_PIN, GPIO.OUT)
pwm = GPIO.PWM(CONTROL_PIN, PWM_FREQ)
pwm.start(0)



ENDPOINT = "things.ubidots.com"
DEVICE_LABEL = "weather-station"
VARIABLE_LABEL = "control"
TOKEN = "BBFF-q2waSOaxZqIvpOsnWpst03B9WA2OLH"
DELAY = 1 # Delay in seconds
URL = "http://{}/api/v1.6/devices/{}/{}/lv".format(ENDPOINT, DEVICE_LABEL, VARIABLE_LABEL)
HEADERS = {"X-Auth-Token": TOKEN, "Content-Type": "application/json"}
def angle_to_duty_cycle(angle=0):
    duty_cycle = (0.05 * PWM_FREQ) + (0.19 * PWM_FREQ * angle / 180)
    return duty_cycle
def motor_control(cmd,change):
    if change!=cmd:
        change=cmd
        if cmd==1:
            dc = angle_to_duty_cycle(90)
            pwm.ChangeDutyCycle(dc)
            time.sleep(2)
        else:
            dc = angle_to_duty_cycle(180)
            pwm.ChangeDutyCycle(dc)
    return change
def get_var(change):
    try:
        attempts = 0
        status_code = 400
        while status_code >= 400 and attempts < 5:
            req = requests.get(url=URL, headers=HEADERS)
            status_code = req.status_code
            attempts += 1
            time.sleep(1)
            #print(req.text)
        change=motor_control(int(float(req.text)),change)
        return change
    except Exception as e:
        print("[ERROR] Error posting, details: {}".format(e))


try:
    change=0
    while True:
        change=get_var(change)
        time.sleep(DELAY)
except KeyboardInterrupt:
    print("Exception: KeyboardInterrupt")
finally:
    GPIO.cleanup()