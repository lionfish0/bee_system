import time
import RPi.GPIO as GPIO

def configure_gpio():
    GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
    GPIO.setup(3, GPIO.OUT)
    GPIO.setup(5, GPIO.OUT)
    
def blink_worker(e):
    t = 2.0
    st = 0.1
    while (True):
        e.wait()
        print("Blink Blink...");
        GPIO.output(5,True)
        time.sleep(st)
        GPIO.output(3,True)
        time.sleep(st)
        GPIO.output(3,False)
        time.sleep(st/2)
        GPIO.output(5,False)
        time.sleep(st/2)
        GPIO.output(3,True)
        time.sleep(st)
        GPIO.output(3,False)
        time.sleep(st)
        time.sleep(t)

