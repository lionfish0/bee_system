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
        self.blocksize = 70
        self.offset = 2
        self.skipcalc = False
    
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
            print("")
            print("")
            print("")
            print("Computing Shift")
            shift = rd.getshift(pair[0].img,pair[1].img)
            print(shift)
            print("Computing output non-flash blocked image")
            out_img = rd.getblockmaxedimage(pair[1].img,self.blocksize,self.offset)
            
            if not self.skipcalc:
                print("Aligning and subtracting")
                done = rd.alignandsubtract(out_img,shift,pair[0].img)
                print("done")
                argmax = done.argmax()
                p = np.array(np.unravel_index(argmax, done.shape))
                print("Peak is at:")
                print(p)
                #diagnostic code (slow but useful?)
                
                print("Diagnostic data being computed")
                maxvals = []
                for it in range(5):
                    print(".")
                    argmax = done.argmax()
                    diagnostic_p = np.array(np.unravel_index(argmax, done.shape))
                    erase_around(done,diagnostic_p[0],diagnostic_p[1])
                    diagnostic_p += 100
                    if (diagnostic_p[0]>=done.shape[0]) or (diagnostic_p[1]>=done.shape[1]):
                        print("error (out of range) diagnostic")
                        continue #can't use this one
                    maxval = done[diagnostic_p[0],diagnostic_p[1]]
                    maxvals.append({'val':maxval, 'location':diagnostic_p.copy()})
                    
                lowresimages = []
                print("Generating low res images")
                for img in [0,1]:
                    print("Image %d" % img)
                    #lowresimages.append(pair[img].img[::10,::10].copy())
                    if img==0:
                        #lowresimages.append(pair[img].img[::10,::10].copy())
                        lowresimages.append(rd.getblockmaxedimage(pair[img].img,10,1)[::10,::10])
                    else:
                        lowresimages.append(out_img[::10,::10]) 
                    #lowresimages.append(rd.getblockmaxedimage(pair[img].img)[::10,::10])
                    
                    
            else:
                print("Skipping compute")
                p = np.array([0,0])
                maxvals = []
                lowresimages = []
                
            #shift in x and y by 100 pixels
            p += 100
            
            print("Location: %d %d" % (p[0],p[1]))
        
            
            print("Computation Complete, saving")  
            highresimages = []
            for img in [0,1]:
                im = pair[img].img
                s = im.shape
                highresimages.append(im[s[0]/2-100:s[0]/2+100,s[1]/2-100:s[1]/2+100].copy())

                
            self.tracking_results.append({'location':p,'lowresimages':lowresimages,'highresimages':highresimages,'maxvals':maxvals})
            pair[0].returnbuffer()
            pair[1].returnbuffer()
