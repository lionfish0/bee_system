import numpy as np
import retrodetect as rd

class Tracking_Control():
    def __init__(self,camera_queue):
        """
        ...
        """
        print("Creating Tracking Object")
        self.camera_queue = camera_queue
        self.tracking_results = []
    
    def get_status_string(self):
        msg = ""
        msg+="Tracking Results: %d" % len(self.tracking_results)
        return msg

    def worker(self):
        while True:
            print("Awaiting image for processing..")
            pair = self.camera_queue.get()
            print("Processing Images")
            shift = rd.getshift(pair[0].img,pair[1].img)
            out_img = rd.getblockmaxedimage(pair[1].img)
            done = rd.alignandsubtract(out_img,shift,pair[0].img)
            p = np.unravel_index(done.argmax(), done.shape)
            
            print("Location: %d %d" % p)
            
            lowresimages = []
            for img in [0,1]:
                lowresimages.append(pair[img].img[::10,::10].copy())
                
            self.tracking_results.append({'location':p,'lowresimages':lowresimages})
            pair[0].returnbuffer()
            pair[1].returnbuffer()
