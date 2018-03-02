from flask import Flask, make_response
from bee_system.blink_control import blink_worker, configure_gpio
from bee_system.camera_control import Camera_Control
import threading
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
import retrodetect as rd
from flask_cors import CORS
import base64

app = Flask(__name__)
CORS(app)

startupdone = False
cam_control = None

@app.route('/startup/<int:exposure>/<int:gain>')
def startup(exposure,gain):
    global startupdone
    if startupdone:
        return "Already Running"
    configure_gpio()
    global run_blink
    run_blink = threading.Event()
    t = threading.Thread(target=blink_worker,args=(run_blink,))
    t.start()
    global cam_control
    cam_control = Camera_Control(exposure,gain)
    cam_control.print_status()
    t = threading.Thread(target=cam_control.worker)
    t.start()
    startupdone = True
    return "Startup complete"

@app.route('/setcamera/<int:exposure>/<int:gain>')
def setcamera(exposure,gain):
    global startupdone
    if not startupdone:
        return "Not online"
    global cam_control
    cam_control.set_exposure(exposure)
    cam_control.set_gain(gain)
    return "Setup complete"

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/start')
def start():
    run_blink.set()
    return "Blinking Started"

@app.route('/nextimage')
def nextimage():
    if not startupdone:
        return "Not online"
    if cam_control.prs.empty():
        return "No new image"
    else:
        pair = cam_control.prs.get()
        pair[0].returnbuffer()
        pair[1].returnbuffer()
        return "done"

    
@app.route('/getcurrentimage/<int:img>/<int:cmax>')
def getcurrentimage(img,cmax):
    if not startupdone:
        return "Not online"
    if cam_control.prs.empty():
        return "No new image"
    if cmax<1 or cmax>255:
        return "cmax parameter must be between 1 and 255."
    if img<0 or img>1:
        return "image must be 0 or 1"
    pair = cam_control.prs.queue[0]#get() #dodgy peekingg
    #msg = ""
    #msg += "%0.5f\n" % (np.mean(pair[0].img))
    #msg += "%0.2f\n" % (np.mean(pair[1].img))
    #return msg
    fig = Figure(figsize=[9,9])
    axis = fig.add_subplot(1, 1, 1)   
    axis.imshow(pair[img].img[::2,::2],clim=[0,cmax])
    #fig.subplots_adjust(left=0, bottom=0, right=1, top=1)
    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    fig.patch.set_alpha(0)
    canvas.print_png(output)
    response = make_response(output.getvalue())

    response.mimetype = 'image/png'
    return response

@app.route('/findretroreflectors')
def findretroreflectors():
    if not startupdone:
        return "Not online"
    pair = cam_control.prs.queue[0]
    shift = rd.getshift(pair[0].img,pair[1].img)
    out_img = rd.getblockmaxedimage(pair[1].img)
    done = rd.alignandsubtract(out_img,shift,pair[0].img)    
    p = np.unravel_index(done.argmax(), done.shape)
    return "Location: %d %d" % p


@app.route('/imagestats')
def imagestats():
    if not startupdone:
        return "Not online"
    if cam_control.prs.empty():
        return "No new image"
    pair = cam_control.prs.queue[0]
    msg = ""
    for img in [0,1]:
        msg+= "Image: %d\n" % img
        msg+= "  Max: %d\n" % np.max(pair[img].img)
        msg+= "  Min: %d\n" % np.min(pair[img].img)
        msg+= " Mean: %0.2f\n" % np.mean(pair[img].img)
    return msg
    
@app.route('/stop')
def stop():
    run_blink.clear()
    return "Blinking Stopped"  
    
@app.route('/shutdown')
def shutdown():
    """
    INCOMPLETE NEEDS TO FREE CAMERA ETC!
    """
    global startupdone
    if startupdone:
        global cam_control
        cam_control.close()
        cam_control = None
        stop()
        global run_blink
        run_blink = None
        startupdone = False
        return "Shutdown Complete"
    else:
        return "System already offline"
    
if __name__ == "__main__":
    app.run(host="0.0.0.0")
