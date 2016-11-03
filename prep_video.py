 # -*- coding: utf-8 -*-
"""
Created on Thu Apr  3 00:16:28 2014
Definitions for RAM RT-video processing 
@author: m
"""



##%% Initializing PulsePal
#import IPython
#IPython.start_ipython()
#%% Parameters
#% parameters for mask based on depth from Kinect
# 155, 150
dodebug=0
parbottom=185   #bottom  of maze;   less=strict shoould be greater than top
partop   =parbottom-12    #top      of maze;   more=strict  
cutx=0 # shift and cut this much from depth-based mask. Coordinates will be too high.
cuty=0
dobgkinect=1 # mask wrong depth?
bowl_sd=.62;
bowl_mag=190;
minblob=200
maxblob=1000
#test_threshold(1,parbottom,partop) 
#dodebug=1;test_blob(1,parbottom,partop,minblob,maxblob) 
#%% imports, capture
global state,trials,curcoord, arms_visited,doors_to_open,curnarm,doors_open,arms_to_visit,sample,daname,out_frame,didtimeout,arms_to_visit
global curnarm, state, arms_visited, doors_to_open,total_narms,frame,center,sample,arms_to_visit,trials
trials=1;
dokinect= 0 # kinect capture?
doweb=    1 # webcam capture?
import numpy as np
import random,os
import time
import cv2
import matplotlib.pyplot as plt
import matplotlib
import pylab
import csv
import httplib, urllib
#import pushover
import thread
import scipy.io as sio
import copy
global frame
#from freenect import sync_get_depth as get_depth, sync_get_video as get_video
dobg=0
debug=0
if dobg:
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
    #    bg = cv2.createBackgroundSubtractorKNN()
    bg = cv2.createBackgroundSubtractorMOG2()
#%%
#%% defs to get position from oat:
import sys
import zmq
import math
import json
def oat_connection_prep():
    #    import os
    # test socket: oat posigen rand2D pos &;oat posisock rep pos 'tcp://*:5555' &
    #os.system("oat posisock rep pos 'tcp://*:5555' &")
    #os.system("oat kill;sh ~/Dropbox/bash/run_oat.sh ")    
    print 'preparing oat connection...'
    global socket,socket_kalman
    
    context = zmq.Context(1)
    
    socket = context.socket(zmq.SUB)
    socket_kalman = context.socket(zmq.SUB)

    print "Connecting to Oat posisock server at tcp://localhost:5550"
    socket.connect("tcp://localhost:5550")
    socket_kalman.connect("tcp://localhost:5551")
    # Subscribe to all
    pos_filter = ""
    
    # Python 2 - ascii bytes to unicode str
    if isinstance(pos_filter, bytes):
        pos_filter = pos_filter.decode('ascii')
    socket.setsockopt_string(zmq.SUBSCRIBE, pos_filter)
    socket_kalman.setsockopt_string(zmq.SUBSCRIBE, pos_filter)
    
    print 'done'
    return socket,socket_kalman
def oat_get_position():
    global  socket,socket_kalman
    reply = socket.recv_string()
    reply_kalman = socket_kalman.recv_string()
    #print "I: Server replied OK (%s)" % reply
    data        = json.loads(reply)
    data_kalman = json.loads(reply_kalman)
    if data['pos_ok']==True and data_kalman['pos_ok']==True	:
#        print data_kalman
        coord= data_kalman['pos_xy']
        sample=data['samp']
        return coord, sample
    else:
        #print 'oat_get_position: Oat reported that position  not ok'
        sample=data['samp']
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
# Define the codec and create VideoWriter object
global cap
#%% captures:
if dokinect:  # kinectw
    pass
elif doweb:   # webcam 
    cap = cv2.VideoCapture(0)


print('Capture:')
print(cap)
#%% READ FUNCTIONS
#%% define mask of radius around center
outer_disk_mask=mask_center(1.6)
def readweb(cap):
	[ret,frame]=cap.read()
	return frame
def read():
    global cap
    global frame
    frame=readweb(cap)
    return frame
frame=read()
if frame==None:
	raise ValueError('Has not found no webcam!')
#for i in range(0,20):
#    _=read()
#%% ===================================        
#%% TEMPLATES START HERE        
# capture a template like so:
frame=read()
cv2.imwrite('templates/new.png', frame)
#%% match template:

global center,armcoords    
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
    #    plt.show()
    return center
def get_match(templatename,img=None):
    if img==None:
        frame=read()
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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

#% GET COORDINATES OF MAZE CENTER
def get_center(frame):
    print 'Getting coordinates of center...'
    templatename="templates/center.png"
    center=get_match(templatename)
    # shift center slighty up
    center=list(center)
    center[1]=center[1]-20
    center=tuple(center)
    # add center circle
    cv2.circle(frame,center, 3, (0,0,255), -1)
    #    cv2.putText(frame,'centr',(center), cv2.FONT_HERSHEY_SIMPLEX, 2,(255,255,255),2,cv2.LINE_AA)
    return center,frame
    
center,frame=get_center(frame)
#% match to arms:
def get_arm_coord(narm):
    templatename="templates/arm"+str(narm)+".png"        
    o=get_match(templatename)
    if dokinect:         # correction for alignment of cameras
        cutx=-7 # cut this much from depth-based mask. Coordinates will be too high.
        cuty=14
        tu=(cutx,cuty)
        o=tuple(map(lambda x, y: x - y, o, tu))
#    print o
    return o 
def get_arm_coords(frame):
    
    frame=read()
    print 'Getting arm coordinates...'
    armcoords=[]
    
    for narm in range (1,13):
#        print narm
        armcoor=get_arm_coord(narm)
        armcoords.append(armcoor)
        cv2.circle(frame,(armcoor), 3, (0,0,255), -1)
        cv2.putText(frame,str(narm),(armcoor), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,0,255),2,cv2.LINE_AA)
        print "arm length",dista(armcoor,center)
    return armcoords,frame
armcoords,frame=get_arm_coords(frame)
#%% read and visualize coordinates of arms and center   
#cv2.putText(frame,'Hit Escape when satisfied',(100,50), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,255,255),2,cv2.LINE_AA)
#cv2.putText(frame,'with arm positions...',(100,100), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,255,255),2,cv2.LINE_AA)
cv2.imshow('Calibrations',frame)
key= cv2.waitKey(30) & 0xff
#if key==27:
#    break

#%% Final read; and release capture so that oat can access it
frame=read()
cap=[]

print 'video prep done, starting oat and socket...'
#%% Get filename using an input box
def get_filename_box():
    import Tkinter as tk
    ## filename entry box
    def displayText():
        """ Display the Entry text value. """
        global entryWidget
        global thefilename
        thefilename=entryWidget.get().strip()
        root.destroy()
        return thefilename
    global thefilename    
    global entryWidget
    root = tk.Tk()
    root.title("Enter Filename")
    root["padx"] = 40
    root["pady"] = 20       
    # Create a text frame to hold the text Label and the Entry widget
    textFrame = tk.Frame(root)
    #Create a Label in textFrame
    entryLabel = tk.Label(textFrame)
    entryLabel["text"] = "Enter filename:"
    entryLabel.pack(side=tk.LEFT)
    # Create an Entry Widget in textFrame
    entryWidget = tk.Entry(textFrame)
    entryWidget["width"] = 50
    entryWidget.pack(side=tk.LEFT)
    textFrame.pack()
    button = tk.Button(root, text="Submit", command=displayText)
    button.pack() 
    root.mainloop()
    return thefilename

 
#%% Oat
print 'Starting Oat... '
os.system(' oat kill; oat clean roi raw pos view_pos_raw  view_pos filt mask kpos  ')

os.system(' oat frameserve wcam raw  &   ')
# os.system(' oat frameserve gige gige_stream  &   ') #% UNCOMMENT ON BRAIN4
# mask and publish to roi:
os.system(' oat framefilt mask raw roi -c  configs/oat/config.toml mask &  ')

## Subtact background: use bsub or mog
os.system('  oat framefilt bsub roi filt -c configs/oat/config.toml bg_config &  ')

#os.system('  oat view filt & ')

## Use color-based object detection on the 'raw' frame stream
## publish the result to the 'pos' position stream
## add --tune after pos here
os.system('  oat posidet hsv filt pos --tune   -c configs/oat/config_wcam.toml hsv_config & ')

os.system(' oat posifilt kalman pos kpos -c configs/oat/config.toml kalman &  ')

os.system(' oat decorate roi -p kpos -s -t view_pos_raw & ') 
#os.system('  oat record -s stream_gige    -d -f /home/m/usb/data/video/movies/fall/   -n ' + thefilename + ' &   ') #% UNCOMMENT ON BRAIN4
#% UNCOMMENT ON BRAIN4
#%% VIEW POSITION:
os.system('  oat view view_pos_raw & ')

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
	#msg= "hello world"
	conn = httplib.HTTPSConnection("api.pushover.net:443")
	conn.request("POST", "/1/messages.json",
  	urllib.urlencode({
   	 "token": "acfZ42h7KMGmAdbzyCBZxkDwTrzhPN",
   	 "user": "uxFdSnAMc9D9kcBdgZWYkW3mwynUvc",
   	 "message": msg,
  	}), { "Content-type": "application/x-www-form-urlencoded" })
	#conn.getresponse()
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
    if not is_near_feeder(curcoord,1):#fromcenter<1500: #then still in center,
        narmout=0
        return narmout
    elif fromcenter>100000: # out of range - tracking error

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
    
#%%        
def is_near_feeder(curcoord,curnarm):        
    global center
    distcutoff = 20000       
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
    edge_cutoff   = 20000       
    #center_cutoff = 700 # it's too scary 
    try:
        dadist=dista(curcoord,center)
        if dadist>edge_cutoff: #or dadist<center_cutoff: 
            is_safe=1
        else:
            is_safe=0
    except:
        is_safe=0
    #print 'is_safe:'+str(is_safe)
    return is_safe
global sample,daname
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
    'ndoors_to_open'
    ]
  
    
def init_data_file(total_narms,ndoors_to_open):    
    global daname,d
#    print daname
#    print('/home/m/usb/data/video/maze_control/fall/'+daname+'.csv')
    
    d=[]
    d.append({"center":center,
              "armcoords" :armcoords,
              "total_narms":total_narms,
              "ndoors_to_open":ndoors_to_open
              })

    return []  
def write_data(arms_visited,diderrors,f):
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
             "sample" :      sample
             })            
    if len(d)<3: # values that do not change        
        f = open('/home/m/usb/data/video/maze_control/fall/'+daname+'_init.csv', 'a')  
        dict_writer = csv.DictWriter(f,keys) 
        dict_writer.writerows(d)  
    else:        # append new rows 
        f = open('/home/m/usb/data/video/maze_control/fall/'+daname+'_rowwise.csv', 'a')  
        dict_writer = csv.DictWriter(f,keys)          
        dict_writer.writerow(d[-1])    
            
#%% Talk to stupid controller
context_stupid = zmq.Context()
socket_pull = context_stupid.socket(zmq.PULL)
port_push='5558'
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

oat_connection_prep()
def getcoor() :
    curcoord,sample=oat_get_position()
    curnarm=which_arm_near(curcoord,armcoords)    
    return curnarm,curcoord,sample
total_narms=12
state='none'
arms_visited=[];arms_to_visit=[]
doors_to_open=random.sample(range(1,total_narms+1), 3) #initial sample,just once
def read_and_show(trials=1,diderrors=[]):
    global pararmcutoff,frame,total_narms
    global curnarm, state, arms_visited, doors_to_open, arms_to_visit,daname
    for i in range (0,trials):
        curnarm,curcoord,sample=getcoor()
        ram_should_continue=stupid_controller_get_status()
        cv2.imshow('frame',frame) # for raw frame observation
        #        cv2.imshow('depth with mask',depth)
        # add some info to frame
        frame_and_info=np.array(frame)
        if math.isnan(curcoord[0])==False : # if rat was identified
            cv2.circle(frame_and_info,(int(curcoord[0]),int(curcoord[1])),20,(0,255,155),1,800)
        cv2.putText(frame_and_info, 'In arm ' + str(curnarm), (20, 450), cv2.FONT_HERSHEY_PLAIN, 2.0, (0, 0, 255), thickness=2)
        cv2.putText(frame_and_info, 'State: ' + state, (20, 50),cv2.FONT_HERSHEY_PLAIN, 2.0, (0, 0, 255),thickness=2)
        cv2.putText(frame_and_info, 'Re-entries: ' + str(diderrors), (20, 150),cv2.FONT_HERSHEY_PLAIN, 2.0, (0, 0, 255),thickness=2)
        if dodebug:
            print 'visited '+ str(arms_visited)
            print 'open    '+ str(doors_to_open)
            print 'arms_to_visit '+ str(arms_to_visit)
        for narm in range(1,total_narms+1):
            yarm=armcoords[narm-1]            
            # draw arms
            if narm not in set(doors_to_open):   # closed
                col=(0,0,0)                 # black
            elif narm in set(arms_visited):      # visited
                col=(0,255,0)               # green
            elif narm in set(arms_to_visit):                                # to visit
                col=(0,0,255)               # red
            else:                                # visited during training, so not arms_to_visit
                col=(255,255,255)           # white
            # draw cutoff for when rat is in arm
#            cv2.circle(frame_and_info,yarm,int(np.sqrt(pararmcutoff)),23,1,1)
            cv2.circle(frame_and_info,yarm, 3, col, -1) # reddot on arm
            cv2.putText(frame_and_info, str(narm), yarm,
                cv2.FONT_HERSHEY_PLAIN, 2.0, col, thickness=2) # number of arm
        cv2.imshow('frame',frame_and_info)
        #print x        
        _= cv2.waitKey(1) & 0xff
        # to save an image: cv2.imwrite('/home/m/im.png', frame)
        return curnarm,curcoord,frame_and_info,sample,ram_should_continue
#curnarm,curcoord,frame_and_info,sample,ram_should_continue=read_and_show()
#%% print to figure
def print2fig(text):
    curnarm,curcoord,frame_and_info,sample,ram_should_continue=read_and_show()
    cv2.putText(frame_and_info, text, (20,80) ,cv2.FONT_HERSHEY_PLAIN, 1.0, (0,255,255),thickness=1)
    cv2.imshow('frame',frame_and_info)
    _= cv2.waitKey(1) & 0xff
def exit_nicely():
    print 'exiting ram nicely.'
#    cv2.destroyAllWindows()
    print 'windows destroyed,sleeping'
    print "killing oat-posisock"
    os.system("killall -2 oat-posisock")
    print "killing oat-record"
    os.system("killall -2 oat-record")    
    print 'killed'
    return    
#%% contains function to determine if visited all necessary arms:
def contains(small, big):
    return set(small)<=set(big)

#global curnarm, state, arms_visited, doors_to_open,total_narms,frame,center,sample,arms_to_visit
    
