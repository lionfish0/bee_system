from flask import Flask
app = Flask(__name__)
from blink_control import blink_worker, configure_gpio
import threading

startupdone = False

@app.route('/startup')
def startup():
    global startupdone
    if startupdone:
        return "Already Running"
    configure_gpio()
    global run_blink
    run_blink = threading.Event()
    t = threading.Thread(target=blink_worker,args=(run_blink,))
    t.start()
    startupdone = True
    return "Startup complete"

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/start')
def start():
    run_blink.set()
    return "Blinking Started"

@app.route('/stop')
def stop():
    run_blink.clear()
    return "Blinking Stopped"    
    
if __name__ == "__main__":
    app.run(host="0.0.0.0")
