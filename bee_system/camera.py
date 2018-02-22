import sys
import time
import numpy as np
from gi.repository import Aravis
import pickle

###TODO Write a class that stores the camera etc
###TODO Rename file to avoid name collision with camera
###Check class methods work with threading

Aravis.enable_interface ("Fake")
try:
    if len(sys.argv) > 1:
        camera = Aravis.Camera.new (sys.argv[1])
    else:
        camera = Aravis.Camera.new (None)
except:
    print ("No camera found")
    exit ()

if camera.is_binning_available():
    print("Camera binning available")
else:
    print("Camera binning NOT AVAILABLE!")
camera.set_region (0,0,2064,1544) #128,128)
camera.set_binning(1,1) #basically disable
camera.set_frame_rate (10.0)
camera.set_exposure_time(5000)
camera.set_gain(300)
camera.set_pixel_format (Aravis.PIXEL_FORMAT_MONO_8)
camera.set_trigger("Line1");

payload = camera.get_payload ()

[x,y,width,height] = camera.get_region ()

print("Camera vendor : %s" %(camera.get_vendor_name ()))
print("Camera model  : %s" %(camera.get_model_name ()))
print("Camera id     : %s" %(camera.get_device_id ()))
print("ROI           : %dx%d at %d,%d" %(width, height, x, y))
print("Payload       : %d" %(payload))
print("Pixel format  : %s" %(camera.get_pixel_format_as_string ()))

stream = camera.create_stream (None, None)

print("Start acquisition")

camera.start_acquisition ()

print("Acquisition")
import ctypes
import numpy as np


for i in range(0,5):
	stream.push_buffer (Aravis.Buffer.new_allocate(payload))


import time
symbol = "$@B\%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "[::-1]

smallbslist = []
for i in range(0,10):
    print("Awaiting image...");
    
    #for i in range(2):
    #    stream.push_buffer (Aravis.Buffer.new_allocate (payload))
    b = [None,None]
    skip = False
    for j in range(2):
        if skip:
            continue
        buffer = stream.pop_buffer ()
        status = buffer.get_status()
        print(status)
        print(int(status))
        if status!=0:
            skip = True
            continue
        if buffer:
            print("buffer ok")
        else:
            print("buffer full?")
        
            
        a = np.frombuffer(buffer.get_data(),dtype="B1").astype(float)
        print("---")
        print(i)
        print(np.mean(a))
        a = np.reshape(a,[1544,2064])
        print(a.shape)
        #b = a[0::18,0::12]
        #b[i] = a[0::36,0::24]
        b[j] = a#[10:50,10:90]
        print("if buffer?")
        if buffer:
            stream.push_buffer (buffer)     
    if skip:
        continue   
    np.set_printoptions(threshold=np.nan) 
#    print(b[1]-b[0])
    diff = b[1]-b[0]
    smalldiff = diff[::18,::12]
    
    smallbs = [b[0][::4],b[1][::4]]
    smallbslist.append(smallbs)
    string = []
    for row in smalldiff:
        for v in row:
            if v>69:
                v=69
            if v<0:
                v=0
            string.append(symbol[int(v)])
        string.append('\n')
    print(''.join(string))
#pickle.dump(smallbslist,open('test_%02d.p'%i,'wb'))
pickle.dump(smallbslist,open('test.p','wb'))

print("Stop acquisition")

camera.stop_acquisition ()

