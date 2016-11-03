 # -*- coding: utf-8 -*-
"""
Created on Thu Apr  3 00:16:28 2014
Definitions for RAM RT-video processing 
@author: m
"""
#%% Parameters
dodebug=0
scale=5 # how to scale frame for display
#%% imports, capture
global state,trials,curcoord, arms_visited,doors_to_open,curnarm,doors_open,arms_to_visit,sample,daname,out_frame,didtimeout,arms_to_visit
global curnarm, state, arms_visited, doors_to_open,total_narms,center,sample,arms_to_visit,trials,poll,socket, socket_kalman
import numpy as np
import pandas as pd
import random,os,tkMessageBox,time,cv2,csv,httplib, urllib,sys,zmq,math,json,copy
import scipy.io as sio
def oat_connection_prep():
    #    import os
    # test socket: oat posigen rand2D pos &;oat posisock rep pos 'tcp://*:5555' &
    #os.system("oat posisock rep pos 'tcp://*:5555' &")
    #os.system("oat kill;sh ~/Dropbox/bash/run_oat.sh ")    
    print 'preparing oat connection...'
    global socket,socket_kalman,poll
    
    context = zmq.Context(1)
    do_kalman=1
    do_sync=0 # use request/reply-based socket? otherwise use asynchronous publisher
    if do_sync:
        print "I: Connecting to Oat server.."
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://localhost:5550")
        poll = zmq.Poller()
        poll.register(socket, zmq.POLLIN)

    else:
        socket = context.socket(zmq.SUB)
        if do_kalman:
            socket_kalman = context.socket(zmq.SUB)
        print "Connecting to Oat posisock server at tcp://localhost:5550"
        socket.connect("tcp://localhost:5550")
        if do_kalman:
            socket_kalman.connect("tcp://localhost:5551")
        pos_filter = ""# Subscribe to all
        if isinstance(pos_filter, bytes):
            pos_filter = pos_filter.decode('ascii')
            socket.setsockopt_string(zmq.SUBSCRIBE, pos_filter)
            if do_kalman:
                socket_kalman.setsockopt_string(zmq.SUBSCRIBE, pos_filter)
                return socket,socket_kalman
            else:
                return socket
def oat_get_position()  :
    global  socket,socket_kalman,poll
    do_kalman=0
    do_sync=0
    if do_sync:
        REQUEST_TIMEOUT = 2500  
        socket.send("nothing")
        socks = dict(poll.poll(REQUEST_TIMEOUT))
        if socks.get(socket) == zmq.POLLIN:
        	reply = socket.recv_string()
    else: 
        reply = socket.recv_string()
    if do_kalman:
        reply_kalman = socket_kalman.recv_string()
    #print "I: Server replied OK (%s)" % reply
    data        = json.loads(reply)
    if do_kalman:
        data_kalman = json.loads(reply_kalman)
        if data['pos_ok']==True and data_kalman['pos_ok']==True	:
            coord= data_kalman['pos_xy']
            sample=data['tick']
            return coord, sample
    elif data['pos_ok']==True 	:
        coord= data['pos_xy']
        sample=data['tick']
        return coord, sample
    else:
        #print 'oat_get_position: Oat reported that position  not ok'
        sample=data['tick']
        return (0,0), sample
                       
def mask_center(radius_division):
    nrows=480;ncols=640
    row, col = np.ogrid[:nrows, :ncols]; cnt_row, cnt_col = nrows / 2, ncols / 2
    mask = ((row - cnt_row)**2 + (col - cnt_col)**2 >(nrows / radius_division)**2)
    return mask
#plt.imshow(mask_center(1.6))     # test the centermask function
#%%
if dodebug:
    try: 
        oat_connection_prep()
        pos,sample=oat_get_position()
        print pos,sample
    except:
        print "error reading socket"
#%%
# run capture through C, save template
# source of this is in ~/Dropbox/maze/pointgrey/strobe/save_template
os.system("~/Dropbox/maze/pointgrey/save_image_gige")
#%% define mask of radius around center
#outer_disk_mask=mask_center(1.6)
def read():
    frame_hd = cv2.imread('/home/m/Dropbox/maze/video/images/gige_template.bmp',0)
    frame  = cv2.resize( frame_hd, (0,0),fx=1.0/scale,fy=1.0/scale ) #resize by 10x
    return frame,frame_hd
frame,frame_hd=read()
if frame is None:
	raise ValueError('Has not found template!')
#for i in range(0,20):
#    _=read()
#%% TEMPLATES START HERE        
# capture a template like so:
cv2.imwrite('/home/m/Dropbox/maze/templates/gige_new_template.png', frame_hd)
#%% match template:

global center,armcoords,ram_should_continue    
def dista(i1,i2):
    x1=i1[0]
    x2=i2[0]
    y1=i1[1]
    y2=i2[1]
    o=(x1-x2)**2+(y1-y2)**2
    return o
def center_from_rectangle(top_left,w,h,img):
    center = (top_left[0] + w/2, top_left[1] + h/2)
    #    cv2.circle(img,center,w/2,1,3,5)
    #    plt.imshow(img,cmap = 'gray')
    #    plt.show()ram_should_continue
    return center
def get_match(templatename,img=None):
    if img==None:
        _,img=read()
        #img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(templatename,0)
    w, h = template.shape[::-1]
    meth='cv2.TM_CCOEFF_NORMED'
    method=eval(meth)
    res = cv2.matchTemplate(img,template,method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc
    center=center_from_rectangle(top_left,w,h,img);
    return center    
#    templatename="/home/m/Dropbox/maze/oram_git/templates/rat/k1.jpg"
#% GET COORDINATES OF MAZE CENTER
def get_center(frame):
    print 'Getting coordinates of center...'
    templatename="/home/m/Dropbox/maze/templates/gige/center.bmp"
    center=get_match(templatename)
    # shift center slighty up
    center=list(center)
    center[1]=center[1]-20
    center=tuple(center)
    # add center circle
    cv2.circle(frame,(center), 30, (255,255,255), -1)
    cv2.putText(frame,"C",(center), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,0,0),2,cv2.LINE_AA)
    #    cv2.putText(frame,'centr',(center), cv2.FONT_HERSHEY_SIMPLEX, 2,(255,255,255),2,cv2.LINE_AA)
    return center,frame
    
center,frame=get_center(frame)
#% match to arms:

def get_arm_coord(narm):
    templatename="/home/m/Dropbox/maze/templates/gige/arm"+str(narm)+".bmp"        
    o=get_match(templatename)
    return o 
def get_arm_coords(frame):
    
    
    print 'Getting arm coordinates...'
    armcoords=[]
    
    center,frame=get_center(frame)
    # add center circle
    cv2.circle(frame,(center[0]/scale,center[1]/scale), 30/scale, (255,255,255), -1)
    #cv2.putText(frame,"C",(center[0]/scale,center[1]/scale), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,0,0),1,cv2.LINE_AA)
    for narm in range (1,13):
        armcoor=get_arm_coord(narm)
        armcoords.append(armcoor)
        cv2.circle(frame,(armcoor[0]/scale,armcoor[1]/scale), 30/scale, (0,255,0), -1)
        cv2.putText(frame,str(narm),(armcoor[0]/scale,armcoor[1]/scale), cv2.FONT_HERSHEY_SIMPLEX, .5,(255,0,0),1,cv2.LINE_AA)
        print "arm length",dista(armcoor,center)
    return armcoords,frame
armcoords,frame=get_arm_coords(frame)
#% read and visualize coordinates of arms and center   
cv2.destroyAllWindows()
cv2.namedWindow("Calibrations", cv2.WINDOW_NORMAL) 
cv2.resizeWindow('Calibrations', 500, 500)
for i in range(1,10):
    cv2.imshow('Calibrations',frame) 
    key= cv2.waitKey(10) 

print 'video prep done, starting oat and socket...'




#%% Get filename using an input box
import Tkinter as tk
import tkMessageBox,random
def get_filename_box()  :
    ## filename entry box
    def displayText():
        """ Display the Entry text value. """
        global entryWidget,entryWidget1,entryWidget2
        global thefilename,itrial,do_stim
        thefilename=entryWidget.get().strip()
        itrial=entryWidget1.get().strip()
        do_stim=entryWidget2.get().strip()
        root.destroy()
        return thefilename,itrial,do_stim
    global thefilename    ,itrial,do_stim
    global entryWidget,entryWidget1,entryWidget2
    root = tk.Tk()
    root.title("Enter Filename")
    root["padx"] = 40
    root["pady"] = 20       
    # Create a text frame to hold the text Label and the Entry widget
    textFrame = tk.Frame(root)
    #Create a Label in textFrame
    entryLabel = tk.Label(textFrame)
    entryLabel1 = tk.Label(textFrame)
    entryLabel2 = tk.Label(textFrame)
    entryLabel["text"] = "Enter rat #:"
    entryLabel1["text"] = "Enter trial #:"
    entryLabel2["text"] = "Extra Stim code (empty for none,1=train,2=test,3=delay):"
    # Create an Entry Widget in textFrame
    entryWidget = tk.Entry(textFrame)
    entryWidget["width"] = 5
    entryWidget1 = tk.Entry(textFrame)
    entryWidget1["width"] = 5
    entryWidget2 = tk.Entry(textFrame)
    entryWidget2["width"] = 5
    textFrame.pack()
    entryLabel.pack(side=tk.LEFT)
    entryWidget.pack(side=tk.LEFT)
    entryLabel1.pack(side=tk.LEFT)
    entryWidget1.pack(side=tk.LEFT)
    entryLabel2.pack(side=tk.LEFT)
    entryWidget2.pack(side=tk.BOTTOM)
    button = tk.Button(root, text="Submit", command=displayText)
    button.pack() 
    root.mainloop()
    if len(do_stim)==0:
        do_stim=0
    else:
        do_stim=int(do_stim)
    if do_stim>10 and do_stim<20:
        stimtype=do_stim-10
        if random.random()>.5:
              do_stim=stimtype
        else: do_stim=0#stimtype+20
        print 'You chose Stochastic do_stim; fate decided do_stim = ', do_stim
        if do_stim>20:
            print('Switch laser to red now!')
            #root = tk.Tk();            tkMessageBox.showwarning('Reminder', 'Switch laser to red now!');root.destroy()
                    
    else:
        print 'Error! do_stim must be less than 20!    '
    if len(itrial)==0:
        itrial=1
    if len(thefilename)==0:
        thefilename='test'
    itrial=int(itrial)
    if itrial<10:
        trialstring=str(0)+str(itrial)
    else:
        trialstring=str(itrial)
    thefilename=thefilename+'_trial'+trialstring
    print thefilename
    #root.destroy()
    #tk.Tk().destroy()
    return thefilename,itrial,do_stim
#
#get_filename_box() # test entry box
#%%
if False:
    #%% simple Oat config for testing
    ppal_cam(0)
    os.system('oat kill')
    os.system('oat clean raw pos view_raw kpos view_pos filt filt_bw preraw raw_dec')
    
    os.system('oat frameserve gige         raw  -c ~/Dropbox/bash/configs/oat/config_gige.toml frameserve-trig &>/dev/null &')
    status=os.WEXITSTATUS(os.system('killall -0 oat-frameserve'))  # check if frameserve is running
    print status
    os.system('oat view  frame raw &')
    
    #%%
    ppal_cam(1)
#%% Oat 
print 'Starting Oat... '
os.system('oat kill')
os.system('killall oat-frameserve')
os.system('oat clean raw pos view_raw kpos view_pos filt filt_bw preraw raw_dec')
status=999
while status!=0:
    os.system('oat frameserve gige        preraw  -c ~/Dropbox/bash/configs/oat/config_gige.toml frameserve-trig &>/dev/null &')
    time.sleep(7)
    status=os.WEXITSTATUS(os.system('killall -0 oat-frameserve'))  # check if frameserve is running
    print status
os.system('oat buffer frame        preraw raw &')
if True: 
    os.system('oat framefilt bsub  raw    filt    &')
    os.system('oat framefilt col   filt   filt_bw -C GREY    &')
else:
    os.system('oat framefilt col   raw    filt_bw -C GREY    &')


# add --tune if you want
os.system('oat posidet   thrsh  filt_bw pos   -c ~/Dropbox/bash/configs/oat/config_gige.toml filt-thr   &')

os.system(' oat posifilt kalman         pos kpos   -c ~/Dropbox/bash/configs/oat/config_gige.toml kalman &  ')

#os.system('oat decorate raw view_pos -s -t  -p pos  &')
os.system('oat decorate raw view_pos -s -t  -p pos -p kpos &')
os.system('oat decorate raw view_raw -s -t          &')

os.system('oat view  frame view_pos -r 15 &')
#%% do i need record here or should i restart every time? Leaning toward here
os.system('oat record  -p pos        -d -f /home/m/video/tracking/ -n rat_gige &')
os.system('oat record -s  view_raw   -d -f /home/m/data/video/movies/   -n rat_gige &')
#% SOCKET TO COMMUNICATE WITH RAM
os.system('oat  posisock pub pos   -e tcp://127.0.0.1:5550 &')
os.system('oat  posisock pub kpos  -e tcp://127.0.0.1:5551 &') # rep or pub (pub is asynchronous)


#%% FOR TESTING ONLY:
#os.system("oat view raw &")
#os.system("oat record raw -s raw -f ~/ -n testta &"  )
#os.system("oat record raw -o -p pos  -f ~/ -n testt &")
#os.system("oat posigen rand2D pos &")
#% SOCKET TO COMMUNICATE WITH RAM
#os.system('oat  posisock pub pos   tcp://127.0.0.1:5550 &')
#os.system('oat  posisock pub kpos  tcp://127.0.0.1:5551 &')
print 'Oat is done, running RAM defs...'
#%% prep arduino UNCOMMENT
#from prep_arduino import argui,argui_thread
#%% RAM settings 
#while retries_left:
#    oat_get_position()
#%% distance (x1-x2)^2-(y1-y2)^2 implementation:

# close door if in arm
def close_when_in():
    global center 
    curcoord=0;
    while dista(curcoord,center)<100:
        curnarm,curcoord,sample=getcoor()
#def send_note(msg):
#	pushover.init("acfZ42h7KMGmAdbzyCBZxkDwTrzhPN")
#	client = pushover.Client("uxFdSnAMc9D9kcBdgZWYkW3mwynUvc")
#	client.send_message(msg, title=msg, priority=1)
import httplib,urllib        
def send_note(msg):
    try:
        conn = httplib.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
                     urllib.urlencode({
                     "token": "acfZ42h7KMGmAdbzyCBZxkDwTrzhPN",
                     "user": "uxFdSnAMc9D9kcBdgZWYkW3mwynUvc",
                     "message": msg,
                     }), { "Content-type": "application/x-www-form-urlencoded" })
    except:pass
#%% look up where he is with leeway: practical implementation    
cv2.destroyAllWindows() 
def which_arm_near(curcoord,armcoords) :
    global center,total_narms
    if math.isnan(curcoord[0]) :
        return float('nan')
    try:        
        fromcenter=dista(curcoord,center)
        #print fromcenter
    except:
        narmout=999
        return  narmout
    if fromcenter<250e3 :#168e3not is_near_feeder(curcoord,1):#fromcenter<1500: #then still in center,
        narmout=0
        return narmout
    elif fromcenter>1.6e6: # out of range - tracking error

        narmout=999
        return  narmout
    else:
        curdist=[]
        for narm in range(1,total_narms+1):
            curdist.append(dista(armcoords[narm-1],curcoord))
        narmout=np.argmin(curdist)+1
        return narmout
                
def iserror(prevnarm,curnarm,arms_to_visit):
    if prevnarm!=curnarm and curnarm!=111 and curnarm!=0 and curnarm!=999:
        if curnarm in arms_to_visit:
            return False    
        else:   
            return True    
    else:
        return False
def check_is_consecutive(l):
    n=1
    return (sum(np.diff(sorted(l)) == 1) >= n) & (all(pd.Series(l).value_counts() == 1))
#%%        
def is_near_feeder(curcoord,curnarm):        
    global center
    distcutoff = 5e5       
    try:
        dadist=dista(curcoord,center)
        #print 'distance from center=' + str(dadist)  
        if dadist>distcutoff and curcoord!=0: 
            is_near=1
        else:
            is_near=0
    except:
        is_near=0
    #print 'is_near feeder:'+str(is_near)
    return is_near
def is_safe_to_control_doors(curcoord):    
    global center
    edge_cutoff   = 250000 
    #center_cutoff = 700 # it's too scary 
    try:
        dadist=dista(curcoord,center)
        if curcoord==(0,0):
            is_safe=0
        elif dadist>edge_cutoff: #or dadist<center_cutoff: 
            is_safe=1
        else:
            is_safe=0
    except:
        is_safe=0
    #print 'is_safe:'+str(is_safe)
    return is_safe
d=[]        
daname=''
# preallocate keys: need all of them that will be saved
keys = ['trials', 
	'xcoord',
	'ycoord', 
	'state',
	'arms_visited', 
	'curnarm', 
	'doors_open',
	'ts','center',
	'armcoords',
	'didtimeout',
	'diderrors',
	'arms_to_visit',
    'daname',
    'sample',
    'total_narms',
    'ndoors_to_open',
    'do_stim',
    'stim_on',
    'lendelay'
    ]
  
    
def init_data_file(total_narms,ndoors_to_open,do_stim,lendelay):    
    global daname,d
#    print daname
#    print('/home/m/data/video/maze_control/fall/'+daname+'.csv')
    
    d=[]
    d.append({"center":center,
              "armcoords" :armcoords,
              "total_narms":total_narms,
              "ndoors_to_open":ndoors_to_open,
              "do_stim":do_stim,
              "lendelay":lendelay #TODO
              })

    return []  
def write_data(arms_visited,diderrors,f,stim_on):
    global d,sample,daname
    d.append({"trials":      trials,
             "xcoord" :       curcoord[0],
             "ycoord" :       curcoord[1],
             "state" :       state,
             "arms_visited": arms_visited,
             "curnarm":      curnarm,
             "doors_open":doors_open,
             "ts":           time.time(),
             "didtimeout":   didtimeout,
             "diderrors":    diderrors,
             "arms_to_visit":      np.array(list(arms_to_visit)),
             "daname"    :   daname,
             "sample" :      sample,
             "stim_on":      stim_on
             })            
    if len(d)<3: # values that do not change        
        f = open('/home/m/maze_control/fall/'+daname+'_init.csv', 'a')  
        dict_writer = csv.DictWriter(f,keys) 
        dict_writer.writerows(d)  
    else:        # append new rows 
        f = open('/home/m/maze_control/fall/'+daname+'_rowwise.csv', 'a')  
        dict_writer = csv.DictWriter(f,keys)          
        dict_writer.writerow(d[-1])    
            
#%% Talk to stupid controller
sys.path.append('/home/m/Dropbox/python/ram/oram_git/')
context_stupid = zmq.Context()
socket_pull = context_stupid.socket(zmq.PULL)
port_push='5562' # port of controller from which to catch exit command 
socket_pull.connect ("tcp://localhost:%s" % port_push)
print "Connected to server with port %s" % port_push
# Initialize poll set
poller = zmq.Poller()
poller.register(socket_pull, zmq.POLLIN)
# Work on requests from both server and publisher
message='none'    
print message
ram_should_continue=True
def stupid_controller_get_status():
    
    global ram_should_continue
    socks = dict(poller.poll(10))
    ram_should_continue=True
    if socket_pull in socks and socks[socket_pull] == zmq.POLLIN:
        print 'receiving...'
        message = socket_pull.recv()
        print "Recieved control command: %s" % message
        if message == "exit": 
            print "RAM Recieved exit command, RAM will stop"
            ram_should_continue=False
        else:
            ram_should_continue=True
        return ram_should_continue
#%% coord and display defs       
###############################################################################        
###############################################################################        
frame,frame_hd=read()

#oat_connection_prep()
def getcoor() :
    curcoord,sample=oat_get_position()
    curnarm=which_arm_near(curcoord,armcoords)
    return curnarm,curcoord,sample
#%%
frame,frame_hd=read()

#import numpy as np;import math,random
total_narms=12
state='none'
arms_visited=[];arms_to_visit=[]
doors_to_open=random.sample(range(1,total_narms+1), 3) #initial sample,just once

#cv2.namedWindow("frame", cv2.WINDOW_NORMAL) 
#cv2.resizeWindow('frame', 500, 500)
def read_and_show(frame,trials=1,diderrors=[],add_text='',Curnarm=[]):
    global pararmcutoff,total_narms
    global state, arms_visited, doors_to_open, arms_to_visit,daname
    #%%
    curnarm_here,curcoord,sample=getcoor()
    Curnarm.append(curnarm_here)
    history_steps=5
    try:
        if np.all( np.equal(curnarm_here, Curnarm[-history_steps:] ) ):
            curnarm=curnarm_here
        else:
            curnarm=Curnarm[-history_steps] # stay on the last value
    except:
        print "Unexpected error:", sys.exc_info()[0]
        curnarm=curnarm_here
    #%%    
    ram_should_continue=stupid_controller_get_status()
    #% add some info to frame
    #frame_and_info=np.array(frame[0]) # but frame_and_info=np.array(frame_hd) 
    if type(frame)==int:
        print frame
    frame_and_info= frame.copy()
    if curcoord!=(0,0): # if rat was identified
                cv2.circle( frame_and_info,(int(curcoord[0]/scale),int(curcoord[1]/scale)), 10, (255,255,255), 15/scale, 300/scale)          
                cv2.circle(frame_and_info,(int(curcoord[0]/scale),int(curcoord[1]/scale)), 30/scale, (0,255,0), -1)
    cv2.putText(frame_and_info, 'In arm ' + str(curnarm), (20/scale, 450/scale), cv2.FONT_HERSHEY_PLAIN, 5.0/scale, (255,255,255), thickness=1)
    cv2.putText(frame_and_info, 'State: ' + state, (20/scale, 150/scale),cv2.FONT_HERSHEY_PLAIN, 5.0/scale, (255,255,255),thickness=1)
    cv2.putText(frame_and_info, 'Re-entries: ' + str(diderrors), (20/scale, 250/scale),cv2.FONT_HERSHEY_PLAIN, 5.0/scale, (255,255,255),thickness=1)
    cv2.putText(frame_and_info, 'Sample: ' + str(sample), (20/scale, 650/scale),cv2.FONT_HERSHEY_PLAIN, 5.0/scale, (255,255,255),thickness=1)
    try:
        cv2.putText(frame_and_info, add_text, (20/scale,550/scale) ,cv2.FONT_HERSHEY_PLAIN, 5.0, (255,255,255),thickness=2)
    except:
        print add_text
    for narm in range(1,total_narms+1):
        yarm=armcoords[narm-1]            
        #            cv2.circle(frame_and_info,yarm, 10, col, -1) # dot on arm
        # color of number correspondns to DOOR status
        if narm not in set(doors_to_open):   # closed
            col_door=(0,0,0)                 # black
        else:
            col_door=(255,255,255)           # open, white
            
        cv2.putText(frame_and_info, str(narm), (int(yarm[0])/scale+80/scale,int(yarm[1]/scale)+80/scale),
                    cv2.FONT_HERSHEY_PLAIN, 1, col_door, thickness=2) # number of arm
        # draw arms - vjsjted corresponds to color of dot
        if narm in set(arms_visited):      # visited
            col=(0,0,0)               # black
        else:# narm in set(arms_to_visit):                                # to visit
            col=(255,255,255)               # white
        cv2.circle( frame_and_info,(int(yarm[0]/scale),int(yarm[1]/scale)), 10/scale, col, 30/scale, 300/scale)
    cv2.imshow('frame',frame_and_info)
    _= cv2.waitKey(2) & 0xff
    #% to save an image: cv2.imwrite('/home/m/im.png', frame)
    return curnarm,curcoord,frame_and_info,sample,ram_should_continue,Curnarm

    
#for i in range(1,100):
#    read_and_show(frame)
    
#%% print to figure
oat_connection_prep()
time.sleep(2)
print 'removing socket...'
socket=[]; socket_kalman=[];
def print2fig(Frame,diderrors,add_text,Curnarm):
    curnarm,curcoord,frame_and_info,sample,ram_should_continue,Curnarm=read_and_show(Frame,1,diderrors,add_text,Curnarm)
def exit_nicely(ppal_cam):
    print 'exiting ram nicely. Stopping camera trigger...'
    ppal_cam(0)
    print 'removing socket...'
    global socket, socket_kalman
    socket=[]; socket_kalman=[];
    #    print "killing oat-posisock"
    #    os.system("killall -2 oat-posisock")
    #    print "killing oat-record"
    #    os.system("killall -2 oat-record")    
    #    print 'killed'
    return    
#%% contains function to determine if visited all necessary arms:
def contains(small, big):
    return set(small)<=set(big)
cv2.destroyWindow("Calibrations") # if calibrations are left open, the window takes too much resourses, buffer overflows
_= cv2.waitKey(10) & 0xff
