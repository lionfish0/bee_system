import time
import RPi.GPIO as GPIO
import multiprocessing

def configure_gpio():
    GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
    GPIO.setup(3, GPIO.OUT)
    GPIO.setup(5, GPIO.OUT)

class Blink_Control:
    def __init__(self,t=2.0):
        self.t = multiprocessing.Value('d',t)
        self.run_blink = multiprocessing.Event()
    
    def worker(self):
        st = 0.03
        while (True):
            self.run_blink.wait()
            print("Blink Blink...(%0.2f)" % self.t.value);
            GPIO.output(5,True)
            time.sleep(st)
            GPIO.output(3,True)
            time.sleep(st)
            GPIO.output(3,False)
            time.sleep(st)
            GPIO.output(5,False)
            time.sleep(st)
            GPIO.output(3,True)
            time.sleep(st)
            GPIO.output(3,False)
            time.sleep(st)
            time.sleep(self.t.value-st*6)

