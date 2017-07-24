### TODO add gige to CSV
## TODO interactive record
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  3 00:16:28 2014
Definitions for RAM RT-video processing
@author: m
"""
#%% Parameters
dodebug=0
is_wcam=True #TODO make conditional
do_gige=True
if is_wcam is True:
    scale  = 1 # how to scale frame for display
    scalet = 5
else:
    scale  = 5
    scalet = 1
#% imports, capture
global state,trials,curcoord, arms_visited,doors_to_open,curnarm,doors_open,arms_to_visit,sample,sample_gige,unique_name,daname,out_frame,didtimeout,arms_to_visit
global curnarm, state, arms_visited, doors_to_open,total_narms,center,arms_to_visit,trials,poll,socket, socket_kalman,socket_gige#,socket_control_wcam,socket_control_gige
import numpy as np
import pandas as pd
import random,os,tkMessageBox,time,cv2,csv,httplib, urllib,sys,zmq,math,json,copy
import scipy.io as sio
unique_name=str(int(round(time.time()*100)))
print 'UNIQUE ID OF THIS SESSION IS: ' + unique_name
def oe_control(command, name):
    ip = '127.0.0.1';    port = 5556;    timeout = 1.;    url = "tcp://%s:%d" % (ip, port)
    context = zmq.Context(1)
    socket_control_oat = context.socket(zmq.REQ)
    socket_control_oat.RCVTIMEO = int(timeout * 1000)  # timeout in milliseconds
    socket_control_oat.connect(url)
    if command is 'start':
        # Start data acquisition
        socket_control_oat.send('StartAcquisition')
        print socket_control_oat.recv()
        socket_control_oat.send('StartRecord'  + ' RecDir=~/usb/data/oe/maze/%s' % name)
        print socket_control_oat.recv()
    elif command is 'stop':
        socket_control_oat.send('StopRecord')
        print socket_control_oat.recv()
# TODO check whether OE is running/needed
#oe_control('start', unique_name)
daname=''
def oat_connection_prep():
    #    import os
    # test socket: oat posigen rand2D pos &;oat posisock rep pos 'tcp://*:5555' &
    #os.system("oat posisock rep pos 'tcp://*:5555' &")
    #os.system("oat kill;sh ~/Dropbox/bash/run_oat.sh ")
    print 'preparing oat connection...'
    global socket,socket_kalman,socket_gige,poll

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
        if do_gige:
            socket_gige = context.socket(zmq.SUB)
        print "Connecting to Oat posisock server at tcp://localhost:5550"
        socket.connect("tcp://localhost:5550")
        if do_kalman: socket_kalman.connect("tcp://localhost:5551")
        if do_gige:   socket_gige.connect("tcp://localhost:5570")
        pos_filter = ""# Subscribe to all
        if isinstance(pos_filter, bytes):
            pos_filter = pos_filter.decode('ascii')
            socket.setsockopt_string(zmq.SUBSCRIBE, pos_filter)
            if do_kalman:
                socket_kalman.setsockopt_string(zmq.SUBSCRIBE, pos_filter)
                if do_gige:
                    socket_gige.setsockopt_string(zmq.SUBSCRIBE, pos_filter)
                    return socket,socket_kalman,socket_gige
                else:
                    return socket,socket_kalman

            else:
                return socket
def oat_get_position()  :
    global  socket,socket_kalman,socket_gige,poll
    do_kalman=0
    do_gige=1
    do_sync=0
    if do_sync:
        REQUEST_TIMEOUT = 2500
        socket.send("nothing")
        socks = dict(poll.poll(REQUEST_TIMEOUT))
        if socks.get(socket) == zmq.POLLIN:
        	reply = socket.recv_string()
    else:
        reply = socket.recv_string()
    if do_kalman:        reply_kalman = socket_kalman.recv_string()
    if do_gige:          reply_gige   = socket_gige.recv_string()
    #print "I: Server replied OK (%s)" % reply
    if do_gige:
        data_gige = json.loads(reply_gige)
        sample_gige=data_gige['tick']
    else:
        sample_gige=0
    data        = json.loads(reply)
    if do_kalman:
        data_kalman = json.loads(reply_kalman)
        if data['pos_ok']==True and data_kalman['pos_ok']==True	:
            coord= data_kalman['pos_xy']
            sample=data['tick']
            return coord, sample,sample_gige
    elif data['pos_ok']==True 	:
        coord= data['pos_xy']
        sample=data['tick']
        return coord, sample,sample_gige
    else:
        #print 'oat_get_position: Oat reported that position  not ok'
        sample=data['tick']
        return (0,0), sample,sample_gige

def mask_center(radius_division):
    nrows=480;ncols=640
    row, col = np.ogrid[:nrows, :ncols]; cnt_row, cnt_col = nrows / 2, ncols / 2
    mask = ((row - cnt_row)**2 + (col - cnt_col)**2 >(nrows / radius_division)**2)
    return mask
#%
# run capture through C or use opencv in case of webcam
# source of this is in ~/Dropbox/maze/pointgrey/strobe/save_template
if is_wcam is False:
    frame_hd = cv2.imread('/home/m/Dropbox/maze/video/images/gige_template.bmp',0)
    os.system("~/Dropbox/maze/pointgrey/save_image_gige")
else:
    os.system("v4l2-ctl --set-ctrl brightness=128")
    os.system("v4l2-ctl --set-ctrl contrast=32")
    os.system("v4l2-ctl --set-ctrl saturation=32")
    os.system("v4l2-ctl --set-ctrl exposure_auto=3")
    #os.system("v4l2-ctl --set-ctrl exposure_absolute=100")
    os.system("v4l2-ctl --set-ctrl sharpness=224")
    time.sleep(.1)
    [_,frame]= cv2.VideoCapture(0).read()
    if frame is None:
        raise ValueError('No webcam!')
#% Save template				 to disk
if is_wcam is False:
    cv2.imwrite('/home/m/Dropbox/maze/templates/gige_new_template.png', frame_hd)
else:
    cv2.imwrite('/home/m/Dropbox/maze/templates/new.png', frame)
#% define mask of radius around center
#outer_disk_mask=mask_center(1.6)
def read():
    if is_wcam is False:
        frame_hd = cv2.imread('/home/m/Dropbox/maze/video/images/gige_template.bmp',0)
        frame  = cv2.resize( frame_hd, (0,0),fx=1.0/scale,fy=1.0/scale ) #resize by 10x
    else:
        frame=cv2.imread('/home/m/Dropbox/maze/templates/new.png', 0)

        frame_hd=frame
    return frame,frame_hd
frame,frame_hd=read()
#for i in range(0,20):
#    _=read()
#%% TEMPLATES START HERE
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
    #if img==None:
    template = cv2.imread(templatename,0)
    _,img=read()
    if is_wcam is True: pass
        #img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        #template  = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
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
#%% GET COORDINATES OF MAZE CENTER
def get_center(frame):
    print 'Getting coordinates of center...'
    if is_wcam is True:
        templatename="/home/m/Dropbox/maze/templates/center.png"
    else:
        templatename="/home/m/Dropbox/maze/templates/gige/center.bmp"
    center=get_match(templatename)
    center=list(center)
    center=tuple(center)
    # add center circle
    cv2.circle(frame,(center), 30, (255,255,255), -1)
    cv2.putText(frame,"C",(center), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,0,0),2,cv2.LINE_AA)
    #    cv2.putText(frame,'centr',(center), cv2.FONT_HERSHEY_SIMPLEX, 2,(255,255,255),2,cv2.LINE_AA)
    return center,frame

center,frame=get_center(frame)
#%% match to arms:


def get_arm_coord(narm):
    if is_wcam is True:
        templatename="/home/m/Dropbox/maze/templates/arm"+str(narm)+".png"
    else:
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

cv2.namedWindow("Calibrations", cv2.WINDOW_NORMAL)
cv2.resizeWindow('Calibrations', 500, 500)
for i in range(1,100):
    cv2.imshow('Calibrations',frame)
    key= cv2.waitKey(10)

print 'video prep done, starting oat and socket...'





#%% Get filename using an input box
import Tkinter as tk
import tkMessageBox,random
#%%
def get_filename_delay()  :
    ## filename entry box
    def displayText():
        """ Display the Entry text value. """
        global entryWidget,entryWidget1,entryWidget2,entryWidget3,entryWidget4 ,entryWidget5,entryWidget6
        global thefilename,itrial,do_stim, delaylen,ntest_arms,stop_if_error,timeout_arm_sec
        thefilename=entryWidget.get().strip()
        itrial=entryWidget1.get().strip()
        do_stim=entryWidget2.get().strip()
        delaylen=entryWidget3.get().strip()
        ntest_arms=entryWidget4.get().strip()
        stop_if_error=int(entryWidget5.get().strip())==1 # convert to logical
        print 'stop_if_error is ', stop_if_error


        timeout_arm_sec=entryWidget6.get().strip()
        root.destroy()
        return thefilename,itrial,do_stim,delaylen,ntest_arms,stop_if_error,timeout_arm_sec
    global thefilename    ,itrial,do_stim,delaylen,ntest_arms
    global entryWidget,entryWidget1,entryWidget2,entryWidget3,entryWidget4,entryWidget5,entryWidget6
    root = tk.Tk()
    root.title("Enter information")
    root["padx"] = 40
    root["pady"] = 20
    # Create a text frame to hold the text Label and the Entry widget
    textFrame = tk.Frame(root)
    #Create a Label in textFrame
    entryLabel = tk.Label(textFrame)
    entryLabel1 = tk.Label(textFrame)
    entryLabel2 = tk.Label(textFrame)
    entryLabel3 = tk.Label(textFrame)
    entryLabel4 = tk.Label(textFrame)
    entryLabel5 = tk.Label(textFrame)
    entryLabel6 = tk.Label(textFrame)
    entryLabel["text"]  = "Rat:"
    entryLabel1["text"] = "Trial:"
    entryLabel2["text"] = "Stim:"
    entryLabel3["text"] = "Delay (min):"
    entryLabel4["text"] = "# training arms:"
    entryLabel5["text"] = "stop_if_error:"
    entryLabel6["text"] = "timeout_arm_sec:"
    # Create an Entry Widget in textFrame
    entryWidget = tk.Entry(textFrame)
    entryWidget["width"] = 5
    entryWidget.insert(tk.END, 'hp')
    entryWidget1 = tk.Entry(textFrame)
    entryWidget1["width"] = 5
    entryWidget2 = tk.Entry(textFrame)
    entryWidget2["width"] = 5
    entryWidget2.insert(tk.END, '0')
    entryWidget3 = tk.Entry(textFrame)
    entryWidget3["width"] = 5
    entryWidget3.insert(tk.END, '1')
    entryWidget4 = tk.Entry(textFrame)
    entryWidget4["width"] = 5
    entryWidget4.insert(tk.END, '10')
    entryWidget5 = tk.Entry(textFrame)
    entryWidget5["width"] = 5
    entryWidget5.insert(tk.END, '1')
    entryWidget6 = tk.Entry(textFrame)
    entryWidget6["width"] = 5
    entryWidget6.insert(tk.END, '60')
    textFrame.pack()
    entryLabel.pack(side=tk.TOP)
    entryWidget.pack(side=tk.TOP)
    entryLabel1.pack(side=tk.TOP)
    entryWidget1.pack(side=tk.TOP)
    entryLabel2.pack(side=tk.TOP)
    entryWidget2.pack(side=tk.TOP)
    entryLabel3.pack(side=tk.TOP)
    entryWidget3.pack(side=tk.TOP)
    entryLabel4.pack(side=tk.TOP)
    entryWidget4.pack(side=tk.TOP)
    entryLabel5.pack(side=tk.TOP)
    entryWidget5.pack(side=tk.TOP)
    entryLabel6.pack(side=tk.TOP)
    entryWidget6.pack(side=tk.TOP)

    button = tk.Button(root, text="Submit", command=displayText)
    button.pack()
    # Run loop
    root.mainloop()

    # Massage entries
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
    delaylen=float(delaylen)*60
    ntest_arms=int(ntest_arms)
    return thefilename,itrial,do_stim,delaylen,ntest_arms,stop_if_error,timeout_arm_sec
#%%
#thefilename,itrial,do_stim,delaylen,ntest_arms=get_filename_delay() # test entry box
#%%
def get_task():
    global beh
    beh=1
    root = tk.Tk()
    radiobuttons = tk.IntVar()
    radiobuttons.set(1)  # initializing the choice, i.e. standard RAM

    tasks = [
        ("Standard",1),
        ("2AFC",2),
        ("2AFC_randomdraw",3),
        ("2AFC_guided_study",4),
        ("Other",5)
    ]
    def radio():
        global beh
        beh=radiobuttons.get()
        print beh
        return beh

    tk.Label(root,
             text="""Choose task:""",
             justify = tk.LEFT,
             padx = 20).pack()

    for txt, val in tasks:
        tk.Radiobutton(root,
                       text=txt,
                       indicatoron=0,
                       padx = 20,
                       variable=radiobuttons,
                       command=radio,
                       value=val).pack(anchor=tk.W)
    #radiobuttons.pack()
    def do_exit():
        root.destroy()
    button = tk.Button(root, text="Submit", command=do_exit)
    button.pack()
    root.mainloop()
    return beh
#beh=get_task();print 'beh is ' , beh
#%% Oat
if is_wcam is True: # Oat for webcam

    os.system(' oat kill; oat clean  -q filt filth pos raw view_raw filt_hsv raw pos view_raw kpos view_pos filt filt_bw preraw raw_dec filt_hsv view_raw roi raw ')

    os.system(' oat frameserve wcam raw  &   ')
    # mask and publish to roi:
    os.system(' oat framefilt mask raw roi -c  ~/Dropbox/bash/configs/oat/config_wcam.toml mask &  ')

    ## Subtact background: use bsub or mog
    os.system('  oat framefilt mog roi filt -c ~/Dropbox/bash/configs/oat/config_wcam.toml bg_config &  ')
    time.sleep(1)
    os.system('oat framefilt col   filt   filt_hsv -C HSV    & ')

    ## Use color-based object detection on the 'raw' frame stream
    ## publish the result to the 'pos' position stream
    ## add --tune after pos here
    os.system('  oat posidet hsv filt_hsv pos --tune -c ~/Dropbox/bash/configs/oat/config_wcam.toml hsv_config_LE & ')

    os.system(' oat posifilt kalman pos kpos -c ~/Dropbox/bash/configs/oat/config_wcam.toml kalman &  ')

    os.system(' oat decorate  roi  view_pos -p kpos -p pos -h -s -t & ') # add -h but only if your oat is new
    os.system(' oat decorate  roi  view_raw  -s -t & ')

    os.system(' oat view  frame view_pos  & ')

    os.system('oat record  -p pos        -d -f /home/m/usb/data/video/tracking/fall/ -n ' +unique_name+ '  rat_wcam &')
    os.system('oat record -s  view_pos  -F H264  -d -f /home/m/usb/data/video/movies/fall/   -n ' +unique_name+ '  rat_wcam &')
    os.system('oat record -s  view_raw  -F H264 -d -f /home/m/usb/data/video/movies/fall/   -n ' +unique_name+ '  rat_raw &')
    #% SOCKET TO COMMUNICATE WITH RAM
    os.system('oat  posisock pub pos   -e tcp://127.0.0.1:5550 &')
    os.system('oat  posisock pub kpos  -e tcp://127.0.0.1:5551 &') # rep or pub (pub is asynchronous)

if do_gige is True: #Oat for GigE
    print 'Starting Oat on GigE... '
    #ppal_cam(1);    time.sleep(.3)
    os.system('oat clean  -q gbw gpos graw gfilt gfilth gfilt gfilth gpos graw gview_raw gfilt_hsv graw gpos gview_raw gkpos gview_pos gfilt gfilt_bw gpreraw graw_dec gfilt_hsv gview_raw graw  view_raw gfilt_hsv graw gpos gview_raw gkpos gview_pos gfilt gfilt_bw gpreraw graw_dec groi gdec')
    #status=9;
    #while status!=0:
    print 'Trying to start gige oat-frameserve'
    os.system('oat frameserve gige gpreraw  -c ~/Dropbox/bash/configs/oat/config_gige.toml frameserve-trig  &')
    os.system('oat buffer    frame   gpreraw  graw &')
    os.system('oat framefilt mask graw groi -c  ~/Dropbox/bash/configs/oat/config_gige.toml mask &  ')
    os.system('oat view frame groi -r 8 &')
    os.system('oat record -p gpos    -d -f /home/m/data/video_gige/tracking/ -n ' +unique_name+ ' rat_gige &')
    os.system('oat record -s  groi   -d -f /home/m/data/video_gige/movies/   -n ' +unique_name+ ' rat_gige -F H264    &')# --rpc-endpoint tcp://127.0.0.1:5572  &') # -F H264 may be too slow, MJPG better

    os.system('oat framefilt col groi   gbw -C GREY    & oat posidet   thresh gbw gpos    -c ~/Dropbox/bash/configs/oat/config_gige.toml filt-thr-dummy   &    ') #make up some positions to get samples
    #os.system('oat posigen rand2D gpos -r 21 &') # make up some positions to get samples
    os.system('oat  posisock pub gpos   -e tcp://127.0.0.1:5570 &')




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
#cv2.destroyAllWindows()
def which_arm_near(curcoord,armcoords) :
    global center,total_narms
    if is_wcam is True:
        distcutoff = 2.5e4
        disterror  = 7.5e4
    else:
        distcutoff = 250e3
        disterror  = 1.6e6
    if math.isnan(curcoord[0]) :
        return float('nan')
    try:
        fromcenter=dista(curcoord,center)
        #print fromcenter
    except:
        narmout=999
        return  narmout
    if fromcenter<distcutoff :#168e3not is_near_feeder(curcoord,1):#fromcenter<1500: #then still in center,
        narmout=0
        return narmout
    elif fromcenter>disterror: # out of range - tracking error

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
#def is_near_feeder(curcoord,curnarm):
#    global center
#    distcutoff = 5e5
#    try:
#        dadist=dista(curcoord,center)
#        #print 'distance from center=' + str(dadist)
#        if dadist>distcutoff and curcoord!=0:
#            is_near=1
#        else:
#            is_near=0
#    except:
#        is_near=0
#    #print 'is_near feeder:'+str(is_near)
#    return is_near
def is_safe_to_control_doors(curcoord):
    global center
    if is_wcam is True:
        edge_cutoff   = 2500
    else:
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
        'unique_name',
        'daname',
        'sample_wcam',
        'sample_gige',
        'total_narms',
        'ndoors_to_open',
        'do_stim',
        'stim_on',
        'lendelay',
        'task'
    ]


def init_data_file(total_narms,ndoors_to_open,do_stim,lendelay,task):
    global unique_name,d,daname
    #    print unique_name
    #    print('/home/m/data/video/maze_control/fall/'+unique_name+'.csv')

    d=[]
    d.append({"center":center,
              "armcoords" :armcoords,
              "total_narms":total_narms,
              "ndoors_to_open":ndoors_to_open,
              "do_stim":do_stim,
              "lendelay":lendelay,
              "task":task,
              "daname":daname,
              })
    return []
def write_data(arms_visited,diderrors,f,stim_on):
    global d,sample,sample_gige,unique_name
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
              "arms_to_visit":      list(arms_to_visit),
              "unique_name"    :   unique_name,
              "daname":           daname,
              "sample_gige" :      sample_gige,
              "sample_wcam" :      sample,
              "stim_on":      stim_on
             })
    if len(d)<3: # values that do not change
        dafname='/home/m/maze_control/fall/'+unique_name+'_init'
        f = open(dafname+'.csv', 'a')
        dict_writer = csv.DictWriter(f,keys)
        dict_writer.writerows(d)
        dj=d[-1]
        print dj
        #dj.arms_to_visit=dj.arms_to_visit.aslist()
        with open(dafname+'.json', 'w') as outfile:
            json.dump(dj,outfile,indent=4,sort_keys=True,separators=(',', ':'))
    else:        # append new rows
        dafname='/home/m/maze_control/fall/'+unique_name+'_rowwise'
        f = open(dafname+'.csv', 'a')
        dict_writer = csv.DictWriter(f,keys)
        dict_writer.writerow(d[-1])
        with open(dafname+'.json', 'a') as outfile:
            json.dump(d[-1],outfile,indent=4,sort_keys=True,separators=(',', ':'))

#%% Talk to stupid controller
sys.path.append('/home/m/Dropbox/python/ram/oram_git/')
context_stupid = zmq.Context()
socket_pull = context_stupid.socket(zmq.PULL)
port_push='5558' # port of controller from which to catch exit command # TODO webcam and gige should be on same button in stupid-controller
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
        if message == "pause":
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
    curcoord,sample,sample_gige=oat_get_position()
    curnarm=which_arm_near(curcoord,armcoords)
    return curnarm,curcoord,sample,sample_gige
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
    global state, arms_visited, doors_to_open, arms_to_visit,unique_name
    #%%
    curnarm_here,curcoord,sample,sample_gige=getcoor()
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
                cv2.circle(frame_and_info, (int(curcoord[0]/scale),int(curcoord[1]/scale)), 10/scalet, (255,255,255), 15, 300/scalet)
                cv2.circle(frame_and_info, (int(curcoord[0]/scale),int(curcoord[1]/scale)), 30/scalet, (0,255,0), -1)
    cv2.putText(frame_and_info, 'In arm ' + str(curnarm), (20/scalet, 450/scalet), cv2.FONT_HERSHEY_PLAIN, 5.0/scalet, (255,255,255), thickness=1)
    cv2.putText(frame_and_info, 'State: ' + state, (20/scalet, 150/scalet),cv2.FONT_HERSHEY_PLAIN, 5.0/scalet, (255,255,255),thickness=1)
    cv2.putText(frame_and_info, 'Re-entries: ' + str(diderrors), (20/scalet, 250/scalet),cv2.FONT_HERSHEY_PLAIN, 5.0/scalet, (255,255,255),thickness=1)
    cv2.putText(frame_and_info, 'Sample: ' + str(sample), (20/scalet, 650/scalet),cv2.FONT_HERSHEY_PLAIN, 5.0/scalet, (255,255,255),thickness=1)
    try:
        cv2.putText(frame_and_info, add_text, (20/scalet,550/scalet) ,cv2.FONT_HERSHEY_PLAIN, 5.0/scalet, (255,255,255),thickness=2)
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

        cv2.putText(frame_and_info, str(narm), (int(yarm[0])/scale+80/scalet,int(yarm[1]/scale)+80/scalet),
                    cv2.FONT_HERSHEY_PLAIN, 1, col_door, thickness=2) # number of arm
        # draw arms - vjsjted corresponds to color of dot
        if narm in set(arms_visited):      # visited
            col=(0,0,0)               # black
        else:# narm in set(arms_to_visit):                                # to visit
            col=(255,255,255)               # white
        cv2.circle( frame_and_info,(int(yarm[0]/scale),int(yarm[1]/scale)), 10/scalet, col, 30/scalet, 300/scalet)
    cv2.imshow('frame',frame_and_info)
    _= cv2.waitKey(2) & 0xff
    #% to save an image: cv2.imwrite('/home/m/im.png', frame)
    return curnarm,curcoord,frame_and_info,sample_gige,sample,ram_should_continue,Curnarm


#for i in range(1,100):
#    read_and_show(frame)

#%% print to figure
oat_connection_prep()
time.sleep(2)
print 'removing socket...'
socket=[]; socket_kalman=[];socket_gige=[]
def print2fig(Frame,diderrors,add_text,Curnarm):
    curnarm,curcoord,frame_and_info,sample_gige,sample,ram_should_continue,Curnarm=read_and_show(Frame,1,diderrors,add_text,Curnarm)
def exit_nicely(ppal_cam):
    #print 'exiting ram nicely. Stopping camera trigger...'
    #ppal_cam(0)
    print 'removing socket...'
    global socket, socket_kalman ,socket_gige
    socket=[]; socket_kalman=[];socket_gige=[]
    #oe_control('stop','')
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
