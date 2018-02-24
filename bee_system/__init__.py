from flask import Flask
app = Flask(__name__)
from bee_system.blink_control import blink_worker, configure_gpio
from bee_system.camera_control import Camera_Control
import threading
import numpy as np

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
    global cam_control
    cam_control = Camera_Control()
    cam_control.print_status()
    t = threading.Thread(target=cam_control.worker)
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

@app.route('/nextimage')
def nextimage():
    if cam_control.prs.empty():
        return "No new image"
    else:
        pair = cam_control.prs.get()
        pair[0].returnbuffer()
        pair[1].returnbuffer()
        return "done"

    
@app.route('/getcurrentimage')
def getcurrentimage():
    if cam_control.prs.empty():
        return "No new image"
    else:
        pair = cam_control.prs.queue[0]#get() #dodgy peekingg
        msg = ""
        msg += "%0.5f\n" % (np.mean(pair[0].img))
        msg += "%0.2f\n" % (np.mean(pair[1].img))
        return msg

@app.route('/stop')
def stop():
    run_blink.clear()
    return "Blinking Stopped"    
    
if __name__ == "__main__":
    app.run(host="0.0.0.0")
