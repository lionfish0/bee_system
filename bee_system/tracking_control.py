import numpy as np
import retrodetect as rd

def erase_around(mat,x,y):
    """
    Erase 5 pixels around x,y in mat (set to zero)
    """
    
    for i in range(max(x-5,0),min(x+5,mat.shape[0])):
        for j in range(max(y-5,0),min(y+5,mat.shape[1])):
            mat[i,j] = 0
    
class Tracking_Control():
    def __init__(self,camera_queue):
        """
        ...
        """
        print("Creating Tracking Object")
        self.camera_queue = camera_queue
        self.tracking_results = []
    
    def get_status_string(self,index):
        if index>=len(self.tracking_results): return "index greater than maximum tracked image"
        
        
        res = self.tracking_results[index]
        msg = ""
        msg+= "Location: %d, %d\nMax value" % (int(res['location'][0]),int(res['location'][1]))
        for mvi,mv in enumerate(res['maxvals']):
            print(mv)
            msg+= "Max value #%d\n" % mvi
            msg+= "Value: %d, Location: %d, %d\n" % (int(mv['val']), int(mv['location'][0]),int(mv['location'][1]))
        return msg

    def worker(self):
        while True:
            print("Awaiting image for processing..")
            pair = self.camera_queue.get()
            print("Processing Images")
            shift = rd.getshift(pair[0].img,pair[1].img)
            out_img = rd.getblockmaxedimage(pair[1].img)
            done = rd.alignandsubtract(out_img,shift,pair[0].img)
            argmax = done.argmax()
            p = np.array(np.unravel_index(argmax, done.shape))
            
            #diagnostic code (slow but useful?)
            
            maxvals = []
            for it in range(5):
                argmax = done.argmax()
                diagnostic_p = np.array(np.unravel_index(argmax, done.shape))
                maxval = done[diagnostic_p[0],diagnostic_p[1]]
                maxvals.append({'val':maxval, 'location':diagnostic_p.copy()})
                erase_around(done,diagnostic_p[0],diagnostic_p[1])
            
            
            #shift in x and y by 100 pixels
            p += 100 
            
            print("Location: %d %d" % (p[0],p[1]))
            
            lowresimages = []
            for img in [0,1]:
                lowresimages.append(pair[img].img[::10,::10].copy())
                
            self.tracking_results.append({'location':p,'lowresimages':lowresimages, 'maxvals':maxvals})
            pair[0].returnbuffer()
            pair[1].returnbuffer()
