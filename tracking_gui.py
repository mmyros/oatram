#!/usr/bin/python
#!/usr/bin/env python2.7
"""
A stupid GUI to control oat-record remotely

Warning: I don't know how to write Python.
"""
from  multiprocessing import Process
import collections,time,tkFont,zmq, sys,os,warnings
import Tkinter as tk
#import matplotlib.pyplot as plt
import numpy as np


#% Connect PulsePal
print 'Connecting PulsePal'
sys.path.append('/home/m/Dropbox/PulsePal/Python/')
from PulsePal import PulsePalObject # Import PulsePalObject
myPulsePal = PulsePalObject() # Create a new instance of a PulsePal object
# Attention! The following line may conflict with Arduinos if one of them is on  '/dev/ttyACM0'
try:
    myPulsePal.connect('/dev/ttyACM0') # Connect to PulsePal on port COM4 (open port, handshake and receive firmware version)
    print(myPulsePal.firmwareVersion) # Print firmware version to the console
    myPulsePal.setDisplay("PYTHON Connected", " Let's do this!")
except:# OSError:
    warnings.warn('No PulsePal found on /dev/ttyACM0!')

#%% Puilse Pal def
def ppal_cam(control):
    if control==1:
        print 'Starting camera trigger...'
        #% start Trigger
        try:
            myPulsePal.programOutputChannelParam('customTrainID',      3, 0)
            myPulsePal.programOutputChannelParam('phase1Voltage',      3, 5)
            myPulsePal.programOutputChannelParam('burstDuration' ,     3, 0)
            myPulsePal.programOutputChannelParam('interBurstInterval', 3, 0)
            myPulsePal.programOutputChannelParam('pulseTrainDelay',    3, 0)
            myPulsePal.programOutputChannelParam('interPulseInterval', 3, .001) # time between stims ( use .001)
            myPulsePal.programOutputChannelParam('phase1Duration',     3, .001) # duration of each stim
            myPulsePal.programOutputChannelParam('pulseTrainDuration', 3, 90200) # How long to stim
            myPulsePal.syncAllParams()
            myPulsePal.triggerOutputChannels(0, 0, 1, 0) # Soft-trigger channel
        except:            pass
    elif control==0:
        #% Trigger off
        try:
            print 'Stopping camera trigger...'
            myPulsePal.programOutputChannelParam('customTrainID',      3, 0)
            myPulsePal.programOutputChannelParam('phase1Voltage',      3, 5)
            myPulsePal.programOutputChannelParam('burstDuration' ,     3, 0)
            myPulsePal.programOutputChannelParam('interBurstInterval', 3, 0)
            myPulsePal.programOutputChannelParam('pulseTrainDelay',    3, 0)
            myPulsePal.programOutputChannelParam('interPulseInterval', 3, 0) # time between stims (.05=20Hz)
            myPulsePal.programOutputChannelParam('phase1Duration',     3, 0) # duration of each stim
            myPulsePal.programOutputChannelParam('pulseTrainDuration', 3, 0) # How long to stim
            myPulsePal.syncAllParams()
            myPulsePal.triggerOutputChannels(0, 0, 1, 0) # Soft-trigger channel
        except:            pass
def ppal_stim(control,pin=4):
    if control==1:
        #% start Trigger
        print 'Starting Pulse Pal stimulation on pin ... ' , pin

        myPulsePal.programOutputChannelParam('customTrainID',      pin, 0)
        myPulsePal.programOutputChannelParam('phase1Voltage',      pin, 5)
        myPulsePal.programOutputChannelParam('burstDuration' ,     pin, 0)
        myPulsePal.programOutputChannelParam('interBurstInterval', pin, 0)
        myPulsePal.programOutputChannelParam('pulseTrainDelay',    pin, 0)
        myPulsePal.programOutputChannelParam('interPulseInterval', pin, 0) # time between stims (.05=20Hz)
        myPulsePal.programOutputChannelParam('phase1Duration',     pin, 999) # duration of each stim
        myPulsePal.programOutputChannelParam('pulseTrainDuration', pin, 90200) # How long to stim
        myPulsePal.syncAllParams()
        if pin==1:
            myPulsePal.triggerOutputChannels(1, 0, 0, 0) # Soft-trigger channel
        elif pin==2:
            myPulsePal.triggerOutputChannels(0, 1, 0, 0) # Soft-trigger channel
        elif pin==3:
            myPulsePal.triggerOutputChannels(0, 0, 1, 0) # Soft-trigger channel
        elif pin==4:
            myPulsePal.triggerOutputChannels(0, 0, 0, 1) # Soft-trigger channel
        stim_is_on=True
        return stim_is_on
    elif control==0:
        #% Trigger off
        print 'Killing Pulse Pal stimulation on pin ... ', pin

        myPulsePal.programOutputChannelParam('customTrainID',      pin, 0)
        myPulsePal.programOutputChannelParam('phase1Voltage',      pin, 5)
        myPulsePal.programOutputChannelParam('burstDuration' ,     pin, 0)
        myPulsePal.programOutputChannelParam('interBurstInterval', pin, 0)
        myPulsePal.programOutputChannelParam('pulseTrainDelay',    pin, 0)
        myPulsePal.programOutputChannelParam('interPulseInterval', pin, 0) # time between stims (.05=20Hz)
        myPulsePal.programOutputChannelParam('phase1Duration',     pin, 0) # duration of each stim
        myPulsePal.programOutputChannelParam('pulseTrainDuration', pin, 0) # How long to stim
        myPulsePal.syncAllParams()
        if pin==1:
            myPulsePal.triggerOutputChannels(1, 0, 0, 0) # Soft-trigger channel
        elif pin==2:
            myPulsePal.triggerOutputChannels(0, 1, 0, 0) # Soft-trigger channel
        elif pin==3:
            myPulsePal.triggerOutputChannels(0, 0, 1, 0) # Soft-trigger channel
        elif pin==4:
            myPulsePal.triggerOutputChannels(0, 0, 0, 1) # Soft-trigger channel
        stim_is_on=False # can make this global for writing into data, but that would complicate workflow
        return stim_is_on

def ppal_pulse(control,pin=4):
    if control==1:
        #% start Trigger
        print 'Starting Pulse Pal pulse stimulation on pin ... ' , pin

        myPulsePal.programOutputChannelParam('customTrainID',      pin, 0)
        myPulsePal.programOutputChannelParam('phase1Voltage',      pin, 5)
        myPulsePal.programOutputChannelParam('burstDuration' ,     pin, 0)
        myPulsePal.programOutputChannelParam('interBurstInterval', pin, 0)
        myPulsePal.programOutputChannelParam('pulseTrainDelay',    pin, 0)
        myPulsePal.programOutputChannelParam('interPulseInterval', pin, .08) # time between stims (.05=20Hz)
        myPulsePal.programOutputChannelParam('phase1Duration',     pin, .05) # duration of each stim
        myPulsePal.programOutputChannelParam('pulseTrainDuration', pin, 90200) # How long to stim
        myPulsePal.syncAllParams()
        if pin==1:
            myPulsePal.triggerOutputChannels(1, 0, 0, 0) # Soft-trigger channel
        elif pin==2:
            myPulsePal.triggerOutputChannels(0, 1, 0, 0) # Soft-trigger channel
        elif pin==3:
            myPulsePal.triggerOutputChannels(0, 0, 1, 0) # Soft-trigger channel
        elif pin==4:
            myPulsePal.triggerOutputChannels(0, 0, 0, 1) # Soft-trigger channel
        stim_is_on=True
        return stim_is_on
    elif control==0:
        #% Trigger off
        print 'Killing Pulse Pal stimulation on pin ... ', pin

        myPulsePal.programOutputChannelParam('customTrainID',      pin, 0)
        myPulsePal.programOutputChannelParam('phase1Voltage',      pin, 5)
        myPulsePal.programOutputChannelParam('burstDuration' ,     pin, 0)
        myPulsePal.programOutputChannelParam('interBurstInterval', pin, 0)
        myPulsePal.programOutputChannelParam('pulseTrainDelay',    pin, 0)
        myPulsePal.programOutputChannelParam('interPulseInterval', pin, 0) # time between stims (.05=20Hz)
        myPulsePal.programOutputChannelParam('phase1Duration',     pin, 0) # duration of each stim
        myPulsePal.programOutputChannelParam('pulseTrainDuration', pin, 0) # How long to stim
        myPulsePal.syncAllParams()
        if pin==1:
            myPulsePal.triggerOutputChannels(1, 0, 0, 0) # Soft-trigger channel
        elif pin==2:
            myPulsePal.triggerOutputChannels(0, 1, 0, 0) # Soft-trigger channel
        elif pin==3:
            myPulsePal.triggerOutputChannels(0, 0, 1, 0) # Soft-trigger channel
        elif pin==4:
            myPulsePal.triggerOutputChannels(0, 0, 0, 1) # Soft-trigger channel
        stim_is_on=False # can make this global for writing into data, but that would complicate workflow
        return stim_is_on

#%%
def start_gui():
    if     (os.statvfs('/home/m/data/video/').f_bfree)<1000000:
        print 'Hey! Youre low on disk space! Wont be able to write raw videos, so exiting'
        time.sleep(4)
        return
    execfile('/home/m/Dropbox/maze/video/oat_connect.py') # starts controllers for communication with oat like stop and start it

    #%% Prep ZMQ
    CTX = zmq.Context()

    RPCInterface = collections.namedtuple('RPC', ['socket',
                                                  'help_cmd',
                                                  'start_cmd',
                                                  'stop_cmd',
                                                  'newfile_cmd',
                                                  'exit_cmd'])
    # Device tuple
    class Device(object):

        def __init__(self, name, addr, help_cmd, start_cmd, stop_cmd, newfile_cmd, exit_cmd):

            self.name = name
            self.is_connected = False
            self.rpc = RPCInterface(CTX.socket(zmq.PUSH), help_cmd, start_cmd, stop_cmd, newfile_cmd, exit_cmd)
            self.req_addr = addr
            self.conn_addr = None

        def connect(self):
            #self.rpc.socket.connect(self.req_addr)
            #socket = self.rpc.socket(zmq.PUSH)
            self.rpc.socket.bind(self.req_addr)
            print("Bound to address"+self.req_addr)
        def disconnect(self):
            self.rpc.socket.disconnect(self.conn_addr)

        def sendMsg(self, request):
            self.rpc.socket.send(request)
            print("[%s] Sent: \'%s\' \n" % (self.name, request.rstrip()))
        def getHelp(self):
            self.sendMsg(self.rpc.help_cmd)

        def sendStart(self):
            self.sendMsg(self.rpc.start_cmd)

        def sendStop(self):
            self.sendMsg(self.rpc.stop_cmd)

        def makeNewFile(self):
            self.sendMsg(self.rpc.newfile_cmd)

        def exit(self):
            self.sendMsg(self.rpc.exit_cmd)

    # Hard-coded devices along with appropriate commands. Add more or remove the ones you don't want
    DEVICES = [
        Device("Webcam tracking", "tcp://127.0.0.1:5557", "help", "start", "pause", "new", "exit"),
        Device("Sliders", "tcp://127.0.0.1:5559", "help", "start", "pause", "new", "exit"),
        Device("Maze control webcam", "tcp://127.0.0.1:5558", "help", "start", "pause", "new", "exit"),
        Device("Open Ephys", "tcp://127.0.0.1:5556", "", "StartRecord", "StopRecord", "NewFile",""),
        Device("Opto stim", "tcp://127.0.0.1:5561", "help", "start", "pause", "new", "exit"),
        Device("Maze control Red", "tcp://127.0.0.1:5562", "help", "start", "pause", "new", "exit"),

    ]

    # Generic remote connction for interacting with a single device
    class RemoteConnection(tk.Frame):

        def __init__(self, parent, device):

            tk.Frame.__init__(self, parent)

            self.parent = parent
            self.font = parent.font

            # Device reference
            self.device = device

            self.initUI()

        def initUI(self):

            # Grid config
            self.columnconfigure(1, weight=1)

            # Label
            label = tk.Label(self, font=self.font, text=self.device.name, width=15, anchor=tk.W)
            label.grid(row=0, column=0, padx=10, sticky=tk.W)

            # Text entry
            entry = tk.Entry(self, font=self.font)
            entry.delete(0, tk.END)
            entry.insert(0, self.device.req_addr)
            entry.grid(row=0, column=1, sticky=tk.W+tk.E)
            entry.bind('<Leave>', lambda event: self.updateEndpoint(event))

            # Connect button
            b_conn_txt = tk.StringVar()
            b_conn_txt.set("Connect")
            b_conn = tk.Button(self, textvariable=b_conn_txt, font=self.font, width=15,
                    command = lambda: self.connect(b_conn_txt, label))
            b_conn.grid(row=0, column=2, padx=10, sticky=tk.E)

        # Connect/Disconnect from remote endpoint
        def connect(self, txt, label):
            if not self.device.is_connected:
                try:
                    print(0)
                    self.device.connect()

                except zmq.ZMQError:
                    self.device.conn_addr = None
                    print ("Failed: Invalid " + self.device.name + " endpoint.")
                    return

                self.device.conn_addr = self.device.req_addr
                self.device.is_connected = True
                label.config(fg='green')
                txt.set("Disconnect")
            else:
                try:
                    self.device.disconnect()
                except zmq.ZMQError:
                    print ("Failed to disconnected from " + self.device.name + " endpoint.")

                self.device.is_connected = False
                label.config(fg='black')
                txt.set("Connect")

        # Udpate socket address
        def updateEndpoint(self, event):

            txt = event.widget.get()
            if txt:
                self.device.req_addr = txt
            else:
                self.device.req_addr = None


    # Basic GUI
    class RemoteControl(tk.Frame):

        def __init__(self, parent):
            tk.Frame.__init__(self, parent)

            self.parent = parent
            self.font = parent.font

            # The connections we are interested in
            self.connections = [RemoteConnection(self, dev) for dev in DEVICES]

            self.initUI()

        def initUI(self):

            self.config(borderwidth=2, relief=tk.RAISED)
            self.pack()

            # Current row counter
            i = 0

            # Connection UIs
            l_connections = tk.Label(self, text="Remote Endpoints", font=self.font)
            l_connections.grid(row=i, column=0)
            i+=1

            start_row = i
            for j,c in enumerate(self.connections):
                i = start_row + j
                c.grid(row=i, column=0, pady=5, sticky="ew")
            i += 1

            b_frame = tk.Frame(self)

            # Record control buttons
            l_connections = tk.Label(self, text="Remote Controls", font=self.font)
            l_connections.grid(row=i, column=0)
            i+=1

            b_help = tk.Button(b_frame, text="Help", font=self.font, command=self.printHelp)
            b_start = tk.Button(b_frame, text="Start", font=self.font, command=self.startRecording)
            b_stop = tk.Button(b_frame, text="Stop", font=self.font, command=self.stopRecording)
            b_new = tk.Button(b_frame, text="New", font=self.font, command=self.makeNewFile)
            b_exit = tk.Button(b_frame, text="Exit", font=self.font, command=self.exitAll)

            b_help.pack(side="left", fill=None, expand=False, padx=10)
            b_start.pack(side="left", fill=None, expand=False, padx=10)
            b_stop.pack(side="left", fill=None, expand=False, padx=10)
            b_new.pack(side="left", fill=None, expand=False,  padx=10)
            b_exit.pack(side="left", fill=None, expand=False, padx=10)

            b_frame.grid(row=i, column=0, sticky="w", padx=10)

        def printHelp(self):
            for i, conn in enumerate(self.connections):
                if conn.device.is_connected:
                    conn.device.getHelp()

        def startRecording(self):
            for i, conn in enumerate(self.connections):
                if conn.device.is_connected:
                    conn.device.sendStart()

        def stopRecording(self):
            for i, conn in enumerate(self.connections):
                if conn.device.is_connected:
                    conn.device.sendStop()

        def makeNewFile(self):
            for i, conn in enumerate(self.connections):
                if conn.device.is_connected:
                    conn.device.makeNewFile()

        def exitAll(self):
            for i, conn in enumerate(self.connections):
                if conn.device.is_connected:
                    conn.device.exit()

    def main():
        def exit_sequence():
            global p1,p2,p3,p4,p5,p6
            p1.terminate()
            p2.terminate()
            p3.terminate()
            p4.terminate()
            p5.terminate()
            p6.terminate()
            print 'terminated'
            os.system(' oat kill &')
            #do_encode=raw_input("Do encoding of video files? enter yes at the end of the day, otherwise no______    ")
            #if do_encode=="yes" :
            #    os.system(' cd ~/data/video/movies;for file in *.avi; do time ffmpeg -y -i "$file" /home/m/box/data/video/movies/"${file%.avi}".mp4; done;   ') # rm *.avi
            #execfile('/home/m/Dropbox/maze/video/maze_analyze/maze_perf.py')
            #ppal_cam(0)
            myPulsePal=[]
            time.sleep(.1)
            root.destroy()
            #os.system("killall python2.7")
        #global root
        root = tk.Tk()
        root.title("Stupid Controller")
        root.font = tkFont.Font(family="Helvetica", size=12)
        root.geometry("590x520+300+300")
        app = RemoteControl(root)
        tk.Button(root, text="Quit stupid controller", command=exit_sequence).pack()
        root.mainloop()


    if __name__ == '__main__':
        main()
#%% definitions for communication with Oat

from  multiprocessing import Process
import collections
import Tkinter as tk
import tkFont
import zmq, sys,os
#import matplotlib.pyplot as plt
import numpy as np
import os,zmq,json
def oat_connection_prep() :

	#os.system("oat kill");	os.system('oat posigen rand2D pos &') #USE ONLY FOR TESTING
	os.system("oat posisock rep pos 'tcp://127.0.0.1:5515' &")
	#os.system("oat kill;sh ~/Dropbox/bash/run_oat.sh ")
	global context,retries_left,oat_client, poll,REQUEST_RETRIES,SERVER_ENDPOINT
	SERVER_ENDPOINT = "tcp://127.0.0.1:5515"

	context = zmq.Context(1)

	print "I: Connecting to Oat server.."
	oat_client = context.socket(zmq.REQ)
	oat_client.connect(SERVER_ENDPOINT)

	poll = zmq.Poller()
	poll.register(oat_client, zmq.POLLIN)

def oat_get_position() :
    global oat_client, poll, retries_left, context,REQUEST_RETRIES,SERVER_ENDPOINT
    oat_client.send("something")
    reply = oat_client.recv_string()
    # PARSE JSON here
    data = json.loads(reply)
    if data['pos_ok']	:
	coord=data['pos_xy']
	return coord
    else:
	print 'oat_get_position: Oat reported that position  not ok'
	return (0,0)
	retries_left = REQUEST_RETRIES
	return coord
#% define clients that will  connect to GUI
def client(port_push):
    context = zmq.Context()
    socket_pull = context.socket(zmq.PULL)
    socket_pull.connect ("tcp://localhost:%s" % port_push)
    print "Connected to server with port %s" % port_push
    # Initialize poll set
    poller = zmq.Poller()
    poller.register(socket_pull, zmq.POLLIN)

    # Work on requests from both server and publisher
    should_continue = True
    while should_continue:
        socks = dict(poller.poll(10))
        if socket_pull in socks and socks[socket_pull] == zmq.POLLIN:
            message = socket_pull.recv()
            print "Recieved control command: %s" % message
            if message == "exit":
                print "Recieved exit command, client will stop"
                should_continue = False
#%% TRACK THE RAT:
import zmq
def oat_frameserve():
    status=999
    while status!=0:
        os.system('oat frameserve   gige   preraw  -c ~/Dropbox/bash/configs/oat/config_gige.toml frameserve-trig &>/dev/null &')
        time.sleep(6)
        status=os.WEXITSTATUS(os.system('killall -0 oat-frameserve'))  # check if frameserve is running
        print status
    os.system('oat buffer frame preraw raw &')

def client_oat_gige_new(port_push): #former client_track; this version uses GigE
    need_to_initialize=1
    if need_to_initialize:
        context = zmq.Context()
        socket_pull = context.socket(zmq.PULL)
        socket_pull.connect ("tcp://localhost:%s" % port_push)
        #print "Connected to server with port %s" % port_push
        # Initialize poll set
        poller = zmq.Poller()
        poller.register(socket_pull, zmq.POLLIN)
        need_to_initialize=0
    # Work on requests from both server and publisher
    should_continue = True
    message='none'
    print message
    while should_continue:
        if message!='none': # we want this to be executed AFTER start only
            pass
        socks = dict(poller.poll(.1))

        if socket_pull in socks and socks[socket_pull] == zmq.POLLIN:
            print 'receiving...'
            message = socket_pull.recv()
            print "Recieved control command: %s" % message
            if message == "start":
                print "Recieved start command, client will open connection with oat and start keeping track of subjects position"
                #oat_connection_prep();
                print 'Starting Oat... '
                os.system(' oat kill; oat clean -q groi gpreraw gpos_dif  graw gpos gfilt_grey gview_raw gfilt_hsv gview_pos_raw  gview_pos gfilt gmask gkpos gpos_thr gpos_hsv ')
                #oat_frameserve()
                os.system(' oat frameserve gige gpreraw  &  oat buffer frame gpreraw gfilt & ')
                # os.system(' oat frameserve gige graw  &  ')
                # mask and publish to roi:
                #os.system(' oat framefilt mask graw groi -c  ~/Dropbox/bash/configs/oat/config.toml gmask &  ')

                ## Subtact background: use bsub or mog
                #os.system(' oat framefilt bsub graw gfilt -c ~/Dropbox/bash/configs/oat/config_gige.toml bg_config &  ')

                ## Use color-based object detection on the 'raw' frame stream
                ## publish the result to the 'pos' position stream
                ## add --tune after pos here

                #os.system('oat framefilt col  gfilt   gfilt_hsv -C HSV    &   oat posidet hsv  gfilt_hsv  gpos     --tune -c ~/Dropbox/bash/configs/oat/config_gige.toml hsv_config_LE & ')
                #os.system('  oat posidet diff gfilt_grey gpos --tune -c ~/Dropbox/bash/configs/oat/config_gige.toml dif_config & ')

                #  THRESH detection
                os.system(' oat framefilt col   gfilt   gfilt_grey -C GREY    & oat posidet thresh gfilt_grey gpos  -c ~/Dropbox/bash/configs/oat/config_gige.toml filt-thr-LE & ')


                #os.system(' oat posifilt kalman gpos gkpos -c ~/Dropbox/bash/configs/oat/config_wcam.toml kalman &  ')

                os.system(' oat decorate  graw  gview_pos -p gpos   -s -t & ') # add -h
                #os.system(' oat decorate  groi  gview_raw -s -t & ') # add -h


                os.system(' oat view  frame gview_pos -r 5  & ')

                #os.system('oat record  -p pos        -d -f /home/m/usb/data/video/tracking/fall/ -n rat_gige &')
                #os.system('oat record -s  view_raw  -F H264 -d -f /home/m/usb/data/video/movies/fall/   -n rat_gige &')

            elif (message == "exit") or (message=="stop"):
                print "Recieved exit command, client will stop keeping track of subjects position"
                #should_continue = False
                os.system("oat kill &")
                message='none'
                need_to_initialize=1

def client_oat(port_push): #former client_track, this uses wcam
    is_wcam=True
    need_to_initialize=1
    if need_to_initialize:
        context = zmq.Context()
        socket_pull = context.socket(zmq.PULL)
        socket_pull.connect ("tcp://localhost:%s" % port_push)
        #print "Connected to server with port %s" % port_push
        # Initialize poll set
        poller = zmq.Poller()
        poller.register(socket_pull, zmq.POLLIN)
        need_to_initialize=0
    # Work on requests from both server and publisher
    should_continue = True
    message='none'
    print message
    while should_continue:
        if message!='none': # we want this to be executed AFTER start only
            pass
        socks = dict(poller.poll(.1))

        if socket_pull in socks and socks[socket_pull] == zmq.POLLIN:
            print 'receiving...'
            message = socket_pull.recv()
            print "Recieved control command: %s" % message
            if message == "start":
                print "Recieved start command, client will open connection with oat and start keeping track of subjects position"
                if is_wcam is True:
                    print 'Starting Oat on webcam... '
                    os.system(' oat kill; oat clean -q filt_grey roi pos_dif  raw pos view_raw filt_hsv view_pos_raw  view_pos filt mask kpos graw gpreraw gview_raw  ')

                    os.system(' oat frameserve wcam raw  &   ')
                    # mask and publish to roi:
                    os.system(' oat framefilt mask raw roi -c  ~/Dropbox/bash/configs/oat/config_wcam.toml mask &  ') #roi

                    ## Subtact background: use bsub or mog, this doesnt work for LEs

                    os.system('  oat framefilt mog roi filt -c ~/Dropbox/bash/configs/oat/config_wcam.toml bg_config &  ')
                    time.sleep(1)

                    os.system(' oat framefilt col   filt   filt_hsv  -C HSV      & ')
                    #os.system(' oat framefilt col   filt   filt_grey -C GREY    & ')

                    ## Use color-based object detection on the 'raw' frame stream
                    ## publish the result to the 'pos' position stream
                    ## add --tune after pos here
                    os.system('  oat posidet hsv  filt_hsv pos      --tune -c ~/Dropbox/bash/configs/oat/config_wcam.toml hsv_config_LE & ')
                    #os.system('  oat posidet diff filt_grey pos_dif --tune -c ~/Dropbox/bash/configs/oat/config_wcam.toml dif_config & ')

                    os.system(' oat posifilt kalman pos kpos -c ~/Dropbox/bash/configs/oat/config_wcam.toml kalman &  ')

                    os.system(' oat decorate  raw  view_pos  -p kpos -p pos -h   -s -t & ') # add -h
                    #os.system(' oat decorate  roi  view_raw -s -t & ') # add -h

                    #os.system(' oat view  frame raw  & ')
                    os.system(' oat view  frame view_pos  & ')

                    os.system('oat record  -p pos        -d -f /home/m/usb/data/video/tracking/fall/ -n rat_wcam &')
                    os.system('oat record -s  view_pos  -F H264  -d -f /home/m/usb/data/video/movies/fall/   -n rat_wcam &')
                    os.system('oat record -s  view_raw  -F H264 -d -f /home/m/usb/data/video/movies/fall/   -n rat_raw &')
                else:
                    ##############------- GIGE section ------------############################
                    #ppal_cam(0);

                    time.sleep(.3)
                    os.system('oat kill;oat clean  -q gpos graw gfilt gfilth gfilt gfilth gpos graw gview_raw gfilt_hsv graw gpos gview_raw gkpos gview_pos gfilt gfilt_bw gpreraw graw_dec gfilt_hsv gview_raw graw  view_raw gfilt_hsv graw gpos gview_raw gkpos gview_pos gfilt gfilt_bw gpreraw graw_dec groi gdec')


                    status=9
                    while status!=0:
                        print 'Trying to start gige oat-frameserve'
                        os.system('oat frameserve gige gpreraw  -c ~/Dropbox/bash/configs/oat/config_gige.toml frameserve-trig  &')
                        time.sleep(4.5)
                        status=os.WEXITSTATUS(os.system('killall -0 oat-frameserve'))  # check if frameserve is running

                    os.system('oat buffer    frame   gpreraw  graw &')


                    os.system(' oat framefilt mask graw groi -c  ~/Dropbox/bash/configs/oat/config_gige.toml mask &  ')
                    os.system('oat framefilt bsub    groi     gfilt   -c ~/Dropbox/bash/configs/oat/config_gige.toml bg_config_LE   &')

                    #os.system('oat framefilt col     gfilt    gfilth -C HSV & oat posidet hsv gfilth gpos  -c ~/Dropbox/bash/configs/oat/config_gige.toml hsv_config_LE  &')


                    os.system('oat framefilt col  gfilt   gfilt_bw -C GREY    & oat posidet   thresh gfilt_bw gpos    -c ~/Dropbox/bash/configs/oat/config_gige.toml filt-thr-LE   &')

                    #os.system(' oat posifilt kalman  gpos      gkpos   -c ~/Dropbox/bash/configs/oat/config_gige.toml kalman   &  ')

                    #os.system('oat decorate    groi gview_pos -s -t    &'); # too slow
                    os.system('oat view frame graw -r 7 &')

                    os.system('oat record  -p gpos        -d -f /home/m/data/video/tracking/ -n rat_gige &')
                    os.system('oat record -s  graw   -d -f /home/m/data/video/movies/   -n rat_gige -F MJPG &') # H264 too slow
                    os.system('oat  posisock pub gpos   -e tcp://127.0.0.1:5550 &')
                    os.system('oat  posisock pub gkpos  -e tcp://127.0.0.1:5551 &') # rep or pub (pub is asynchronous)


                    ppal_cam(1)

            elif (message == "exit") or (message=="stop"):
                print "Recieved exit command, client will stop keeping track of subjects position"
                #should_continue = False
                os.system("oat kill &")
                message='none'
                need_to_initialize=1

#%% MAZE RAM control
#try:
from prep_arduino import argui,closeall,openall,moveall,close_slowly

#%% Webcam-based control
def client_ram_wcam(port_push,closeall,openall,moveall,close_slowly,ppal_cam):

    sys.path.append('/home/m/Dropbox/python/ram/oram_git/')
    context = zmq.Context()
    socket_pull = context.socket(zmq.PULL)
    socket_pull.connect ("tcp://localhost:%s" % port_push)
    print "Connected to server with port %s" % port_push
    # Initialize poll set
    poller = zmq.Poller()
    poller.register(socket_pull, zmq.POLLIN)

    # Work on requests from both server and publisher
    global ram_should_continue
    global behavioral_task
    video_started=0
    ram_should_continue = True
    message='none'
    print message
    while ram_should_continue:
        socks = dict(poller.poll(10))
        if socket_pull in socks and socks[socket_pull] == zmq.POLLIN:
            print 'receiving...'
            message = socket_pull.recv()
            print "Recieved control command: %s" % message
            #% Actual RAM control and show. This can also be done on start of ram - then will have to wait twice before keystrokes though


            if message == "start":
                # TODO start OE recording first so that it sees the first camera timestamp
                print "Recieved start command, client will prepare maze for RAM or 2AFC"
                import prep_ram_wcam_or_gige

                ppal_cam(1);	time.sleep(.2)    ;	#ppal_cam(0) #%% briefly trigger camera to get background, make sure it works
                prep_ram_wcam_or_gige.ram_2AFC(closeall,openall,moveall,close_slowly,1,ppal_stim,ppal_cam)
                #socket_control_gige ,socket_control_wcam=prep_ram_wcam_or_gige.oat_record_control_init()
                #prep_ram_wcam_or_gige.oat_record_control( 's',socket_control_gige)
            elif message == "new" :
                prep_ram_wcam_or_gige.ram_2AFC(closeall,openall,moveall,close_slowly,1,ppal_stim,ppal_cam)
                #prep_ram_wcam_or_gige.oat_record_control( 'n',socket_control_gige)

            elif message == "pause":
                #prep_ram_wcam_or_gige.oat_record_control( 'p',socket_control_gige)
                message='none'
            elif message == "exit":
                del prep_ram_wcam_or_gige
                os.system('oat kill ')
                message='none'
                # TODO stop OE recording, too

# Webcam-based control that tracks red tether:
def client_ram_gige_stim(port_push,closeall,openall,moveall,close_slowly,ppal_cam):
    sys.path.append('/home/m/Dropbox/python/ram/oram_git/')
    context = zmq.Context()
    socket_pull = context.socket(zmq.PULL)
    socket_pull.connect ("tcp://localhost:%s" % port_push)
    print "Connected to server with port %s" % port_push
    # Initialize poll set
    poller = zmq.Poller()
    poller.register(socket_pull, zmq.POLLIN)

    # Work on requests from both server and publisher
    global ram_should_continue
    global behavioral_task
    video_started=0
    ram_should_continue = True
    message='none'
    print message
    while ram_should_continue:
        socks = dict(poller.poll(10))
        if socket_pull in socks and socks[socket_pull] == zmq.POLLIN:
            print 'receiving...'
            message = socket_pull.recv()
            print "Recieved control command: %s" % message
            #% Actual RAM control and show. This can also be done on start of ram - then will have to wait twice before keystrokes though

            if message == "start":
                # TODO start OE recording first so that it sees the first camera timestamp
                print "Recieved start command, client will prepare maze for RAM or 2AFC"
                import prep_ram_wcam_or_gige_red

                ppal_cam(1);    #%%  trigger camera 
                prep_ram_wcam_or_gige_red.ram_2AFC(closeall,openall,moveall,close_slowly,1,ppal_stim,ppal_cam)
                #socket_control_gige ,socket_control_wcam=prep_ram_wcam_or_gige.oat_record_control_init()
                #prep_ram_wcam_or_gige.oat_record_control( 's',socket_control_gige)
            elif message == "new" :
                prep_ram_wcam_or_gige_red.ram_2AFC(closeall,openall,moveall,close_slowly,1,ppal_stim,ppal_cam)
                #prep_ram_wcam_or_gige.oat_record_control( 'n',socket_control_gige)

            elif message == "pause":
                #prep_ram_wcam_or_gige.oat_record_control( 'p',socket_control_gige)
                message='none'
            elif message == "exit":
                del prep_ram_wcam_or_gige_red
                os.system('oat kill ')
                message='none'
                # TODO stop OE recording, too

def ram_sliders(port_push,argui_function,openall,closeall):
    context = zmq.Context()
    socket_pull = context.socket(zmq.PULL)
    socket_pull.connect ("tcp://localhost:%s" % port_push)
    print "Connected to server with port %s" % port_push
    # Initialize poll set
    poller = zmq.Poller()
    poller.register(socket_pull, zmq.POLLIN)    # Work on requests from both server and publisher
    should_continue = True
    message='none'
    print message
    while should_continue:
        socks = dict(poller.poll(10))

        if socket_pull in socks and socks[socket_pull] == zmq.POLLIN:
            print 'receiving...'
            message = socket_pull.recv()
            print "Recieved control command: %s" % message
            if message == "start":
                argui_function()
            if message == "new":
                openall()
            if message == "pause":
                closeall()



#%% Client oat
def client_stim(port_push):
    context = zmq.Context()
    socket_pull = context.socket(zmq.PULL)
    socket_pull.connect ("tcp://localhost:%s" % port_push)
    print "Connected to server with port %s" % port_push
    # Initialize poll set
    poller = zmq.Poller()
    poller.register(socket_pull, zmq.POLLIN)


    # Work on requests from both server and publisher
    should_continue = True
    message='none'
    print message
    while should_continue:
        socks = dict(poller.poll(10))

        if socket_pull in socks and socks[socket_pull] == zmq.POLLIN:
            print 'receiving...'
            message = socket_pull.recv()
            print "Recieved control command: %s" % message
            if (message == "start"):
                ppal_stim(1)
            if (message == "new"):
                ppal_pulse(1)
            if message == "pause":
                ppal_stim(0)
#%% Client oat

def client_oat_gige(port_push): # currently unused
    context = zmq.Context()
    socket_pull = context.socket(zmq.PULL)
    socket_pull.connect ("tcp://localhost:%s" % port_push)
    print "Connected to server with port %s" % port_push
    # Initialize poll set
    poller = zmq.Poller()
    poller.register(socket_pull, zmq.POLLIN)


    # Work on requests from both server and publisher
    should_continue = True
    message='none'
    print message
    while should_continue:
        socks = dict(poller.poll(10))

        if socket_pull in socks and socks[socket_pull] == zmq.POLLIN:
            print 'receiving...'
            message = socket_pull.recv()
            print "Recieved control command: %s" % message
            if message == "start":
                print "Recieved start command, client will start Oat"
                print "Make sure OE is recording"
                #%%
                os.system('oat kill')
                os.system('killall oat-frameserve')

                os.system('oat clean -q view_raw filt_hsv raw pos view_raw  kpos view_pos filt preraw raw_dec')
                oat_frameserve()
                if True:
                    os.system('oat framefilt bsub  raw  filt    &')
                    os.system('oat framefilt col   filt  filt_bw -C GREY    &')
                else:
                    os.system('oat framefilt col   raw  filt_bw -C GREY    &')

                ppal_cam(1)

                os.system('oat posidet thrsh filt_bw pos --tune -c ~/Dropbox/bash/configs/oat/config_gige.toml filt-thr   &')

                os.system('oat decorate raw view_pos -s -t  -p pos  &')
                os.system('oat decorate raw view_raw -s -t          &')

                os.system('oat view  frame view_pos -r 15 &')
                #%%
                os.system('oat record  -p pos        -d -f /home/m/data/video/tracking/ -n rat_gige &')
                os.system('oat record -s  view_raw   -d -f /home/m/data/video/movies/   -n rat_gige &')

            elif message == "pause":

                print "Turning off trigger"
                #ppal_cam(0) # stop trigger camera
            elif message == "new" :

#                print "killing old recording"
#                os.system("killall -2 oat-record")
#                time.sleep(2)
                print "starting camera trigger "
                ppal_cam(1) # start trigger camera

                # RECORD VIDEO
#                os.system('  oat record -s  raw   -d -f /home/m/data/video/movies/ -n rat_gige &  ')

                ## RECORD POSITION
                # Save frame stream 'raw' and positional stream 'pos'
#                os.system('  oat record  -p pos -d -f /home/m/data/video/tracking/ -n rat_gige &  ')
#                time.sleep(2)
#                ppal_cam(0) # stop trigger camera
            elif message == "exit":
                #ppal_cam(0) # stop trigger camera

                print "Recieved exit command, client will stop"
                #should_continue = False
                os.system(' oat kill ')

#%% start clients. Maybe do this inside GUI somehow? Or maybe exit doenst quit the client, just resets settings and does oat-kill
global p1,p2,p3,p4,p5,p6
p1=Process(target=client_oat, args=('5557',))
p2=Process(target=ram_sliders, args=('5559',argui,openall,closeall))
p3=Process(target=client_ram_wcam,        args=('5558',closeall,openall,moveall,close_slowly,ppal_cam,))
#p3=Process(target=client_ram,   args=('5558',))
p4=Process(target=client, args=('5556',))
p5=Process(target=client_stim, args=('5561',))
p6=Process(target=client_ram_gige_stim,   args=('5562',closeall,openall,moveall,close_slowly,ppal_cam,))
p1.start()
p2.start()
p3.start()
p4.start()
p5.start()
p6.start()
#%% start GUI/server
Process(target=start_gui).start()
