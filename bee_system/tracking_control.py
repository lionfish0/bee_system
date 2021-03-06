import numpy as np
import retrodetect as rd
import time
from multiprocessing import Queue, Value
import threading
from datetime import datetime as dt

def ascii_draw(mat):
    symbols = np.array([s for s in ' .,:-=+*X#@@'])[::-1]
    msg = ""    
    mat = (11*mat/(np.max(mat)+1)).astype(int)
    mat[mat<0] = 0
    for i in range(0,len(mat),2):
        msg+=''.join(symbols[mat][i])+"\n"
    return msg

def score_img(mat):
    width = min(mat.shape[0],mat.shape[1]) 
    if width<14: #can't check a circle around the point - more importantly we don't know where the middle is
        return 0
    a = np.linspace(0,2*np.pi,16)
    xs = width/2 + 4*np.cos(a)
    ys = width/2 + 4*np.sin(a)    
    m = -255
    for x,y in zip(xs.astype(int),ys.astype(int)):
        #if x<0: continue
        #if y<0: continue
        #if x>mat.shape[0]: continue
        #if y>mat.shape[1]: continue
        m = max(m,mat[x,y])
    return np.max(mat) - m
        
def erase_around(mat,x,y,extent=20):
    """
    Erase [default 20] pixels around x,y in mat (set to zero).
    Returns these pixels
    """
    #print("Erasing around %d,%d" % (x,y))
    startx = x-extent
    endx = x+extent
    starty = y-extent
    endy = y+extent
    if startx<0: startx=0
    if starty<0: starty=0
    if startx>mat.shape[0]: startx=mat.shape[0]
    if starty>mat.shape[1]: starty=mat.shape[1]    
    erased_pixels = mat[startx:endx,starty:endy].copy()
    mat[startx:endx,starty:endy] = -255
    
  #  #TODO replace loop implementation with numpy array access
  #  for i in range(max(x-erase_extent,0),min(x+erase_extent,mat.shape[0])):
  #      for j in range(max(y-erase_extent,0),min(y+erase_extent,mat.shape[1])):
  #          mat[i,j] = 0
    
    return erased_pixels
    
    
class Tracking_Control():
    def __init__(self,camera_queue,tracking_results=[]):
        """
        ...
        """
        print("Creating Tracking Object")
        self.camera_queue = camera_queue
        self.tracking_results_queue = Queue()
        self.tracking_results = tracking_results
        self.blocksize = Value('i',30)
        self.offset = Value('i',2)
        self.stepsize = Value('i',10)
        self.skipcalc = Value('b',False)
        self.searchcount = Value('i',1)
        self.startx = Value('i',100)
        self.starty = Value('i',100)
        self.endx = Value('i',100)
        self.endy = Value('i',100)
                
        t = threading.Thread(target=self.fill_tracking_results)
        t.start()
    def fill_tracking_results(self):
        """Just moves stuff from the queue into the list"""
        while True:
            self.tracking_results.append(self.tracking_results_queue.get())
    
    def get_status_string(self,index):
        if index>=len(self.tracking_results): return "index greater than maximum tracked image"
        
        
        res = self.tracking_results[index]
        msg = ""
        for mvi,mv in enumerate(res['maxvals']):
            msg+= "--------\n"
            msg+= "Max value #%d\n" % mvi
            msg+= "Value: %d, Location: %d, %d\n" % (int(mv['val']), int(mv['location'][0]),int(mv['location'][1]))
        return msg

    def worker(self):
        import os
        os.nice(20) #these shouldn't be priorities
        searchbox = 100
        while True:
            #Awaiting image for processing [blocking]
            print("Waiting for image from camera control...(skipcalc=%d)" % self.skipcalc.value)
            pair = self.camera_queue.get()
            starttime = time.time()
            msg = ""

            msg += "Saving data:\n"
            msg += "time: %0.4f\n" % (time.time()-starttime)
            print(pair[0]['raw'])
            timestr = time.strftime("%Y%m%d_%H:%M:%S")
            np.save(open('raw_%s_0.np' % timestr,'wb'),pair[0]['raw'].astype(np.byte))
            msg += "time: %0.4f\n" % (time.time()-starttime)
            np.save(open('raw_%s_1.np' % timestr,'wb'),pair[1]['raw'].astype(np.byte))
            msg += "time: %0.4f\n" % (time.time()-starttime)
            msg += "Done\n"
            msg += "Processing Images\n"
            msg += "time: %0.4f\n" % (time.time()-starttime)
            msg += "Computing Shift (stepsize=%d)\n" % self.stepsize.value
            shift = rd.getshift(pair[0]['raw'],pair[1]['raw'],step=self.stepsize.value,searchbox=searchbox)
            msg += "    shift: %d %d\n" % (shift[0], shift[1])
            msg += "time: %0.4f\n" % (time.time()-starttime)
            msg += "Computing output non-flash blocked image\n"
            if not self.skipcalc.value:
                out_img = rd.getblockmaxedimage(pair[1]['raw'],self.blocksize.value,self.offset.value)
            else:
                out_img = pair[1]['raw']
                
            msg += "time: %0.4f\n" % (time.time()-starttime)
            
            if not self.skipcalc.value:
                msg+="Aligning and subtracting\n"
                start = np.array([self.startx.value,self.starty.value])
                end = np.array(out_img.shape)-np.array([self.endx.value,self.endy.value])
                
                done = rd.alignandsubtract(out_img,shift,pair[0]['raw'])#,start=start,end=end)
                msg += "time: %0.4f\n" % (time.time()-starttime)
                
                maxvals = []
                for it in range(self.searchcount.value):
                    #print(".")
                    argmax = done[start[0]-searchbox:end[0]-searchbox,start[1]-searchbox:end[1]-searchbox].argmax()
                    p = np.array(np.unravel_index(argmax, done.shape))
                    p+=start-searchbox
                    
                    maxval = done[p[0],p[1]]
                    peak_sample_img = erase_around(done,p[0],p[1])
                    score = score_img(peak_sample_img)
                    p += searchbox
                    if (p[0]>=done.shape[0]) or (p[1]>=done.shape[1]):
                        #print("error (out of range) location")
                        msg+="  [error (out of range) location]\n"
                        continue #can't use this one
                    
                    maxvals.append({'val':maxval, 'location':p.copy(), 'sample_img':peak_sample_img,'score':score})
                    msg += " - Preparing stats"
                    msg += "peak at [%d, %d] = %d [score=%0.5f]\n" % (p[0],p[1],maxval,score)
                    msg += ascii_draw(peak_sample_img)
                    msg += "\n"
                    msg += "time: %0.4f\n" % (time.time()-starttime)
                 
                msg += "time: %0.4f\n" % (time.time()-starttime)                    
                lowresimages = []
                #print("Generating low res images")
                msg += " - Generating low res images\n"
                for img in [0,1]:
                    #print("Image %d" % img)
                    #lowresimages.append(pair[img][::10,::10].copy())
                    if img==0:
                        im = pair[img]['raw'][::10,::10].copy()
                        
                        scalestart = (start/10).astype(int)
                        scaleend = (end/10).astype(int)
                        
                        im[scalestart[0],scalestart[1]:scaleend[1]] = 255
                        im[scaleend[0],scalestart[1]:scaleend[1]] = 255
                        lowresimages.append(im)
                    else:
                        im = rd.shiftimg(out_img,shift,cval=255)[::10,::10].copy()
                        lowresimages.append(im) 
                    msg += "time: %0.4f\n" % (time.time()-starttime)   
            else:
                maxvals = []
                lowresimages = []
                shift = [np.nan,np.nan]
                
            
            msg += "Computation Complete, recording\n"
            msg += "time: %0.4f\n" % (time.time()-starttime)                    

            highresimages = []
            for img in [0,1]:
                im = pair[img]['raw']
                if img == 1:
                    im = rd.shiftimg(im,shift,cval=255)
                s = im.shape
                highresimages.append(im[int(s[0]/2-100):int(s[0]/2+100),int(s[1]/2-100):int(s[1]/2+100)].copy())
            msg += "time: %0.4f\n" % (time.time()-starttime)
            msg += "datetime0: %s\n" % pair[0]['datetime'].strftime("%Y-%m-%dT%H:%M:%S.%f")
            msg += "datetime1: %s\n" % pair[1]['datetime'].strftime("%Y-%m-%dT%H:%M:%S.%f")
            #self.tracking_results.append({'lowresimages':lowresimages,'highresimages':highresimages,'maxvals':maxvals,'shift':shift})
            self.tracking_results_queue.put({'lowresimages':lowresimages,'highresimages':highresimages,'maxvals':maxvals,'shift':shift,'msg':msg,'dt0':pair[0]['datetime'].strftime("%Y-%m-%dT%H:%M:%S.%f"),'dt1':pair[1]['datetime'].strftime("%Y-%m-%dT%H:%M:%S.%f")})
             
            
            

            #msg += "time: %0.4f\n" % (time.time()-starttime)    
            #    
            #msg += "Recording Complete\n Returning Buffers\n"
            #pair = None #erase
#            pair[0].returnbuffer()
#            pair[1].returnbuffer()
            pair = None
            #msg += "time: %0.4f\n" % (time.time()-starttime)    
            #msg += "Buffers returned\n"            
            #self.tracking_results[-1]['msg'] = msg
            print("Processing Complete")

