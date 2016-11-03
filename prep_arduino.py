"""
Created on Mon Feb 24 18:16:02 2014

@author: root
"""

#%% init 
do_debug=0
from pyfirmata import Arduino, util
from Tkinter import *
import time as t
#ls '/dev/ttyA*'
print '===================================='
boards_found=0
indport=0 # start at -1 if no pulsepal is expected. PulsePal should be connected first, so it will be presumably on ACM0.
board1=[]
board2=[]
while indport<5 and boards_found<2 :        
    if boards_found <1 :
        print 'Looking for board 1...'
        board1 = []
        try:
            indport=indport+1
            board1 = Arduino('/dev/ttyACM'+str(indport))
            boards_found += 1
        except Exception as e:        
            sys.exc_clear()
            pass
    else:
        print 'Found board 1 on port ttyACM' + str(indport)
        board1
        print 'Looking for board 2...'
        board2 = []
        try:
            indport=indport+1
            board2 = Arduino('/dev/ttyACM'+str(indport))
        except Exception as e:
            sys.exc_clear()
            pass
        print 'Found board 2 on port ttyACM' + str(indport) + '. We"re in business!!'
        board2
        print '===================================='
        boards_found += 1
# pins 2 to 9 (so subtract 1 from arduino pin to get software pin)
#%% function that controls arduino
def a (board,pin , value):
    """ pin , value
    """
    if board==1:
        board1.digital[pin].write(value)
    else:
        board2.digital[pin].write(value)
    #return 0

#% define the blink function    
def blink(board):
    a(board, 4, 0);
    t.sleep(1)
    a(board, 4, 1);
    t.sleep(1)
def blinkfast(board):
    for x in range(0, 12):
        a(board, 4, 0);
        t.sleep(.1)
        a(board, 4, 1);
        t.sleep(.1)
def blinkfast13():
    for x in range(0, 12):
        a(board, 13, 0);
        t.sleep(.1)
        a(board, 13, 1);
        t.sleep(.1)
#%% main function that will run in the thread:    
def mainfun():
    argui()
#    ram_6_2(15)    
#    maze1();
if do_debug:    
    print 'blinking board 1...'    
    blinkfast(1) # check connection to arduino
    print 'blinking board 2...'    
    blinkfast(2) # check connection to arduino
    print 'Did they blink? Then all is dandy'    
    print 'Otherwise, disconnect the arduino, plug in first then second, then re-run prep_arduino.py'
#% control a servo
#% set up pinlist_board1 as a bunch of servo objects
pinlist_board1=[];
pinlist_board2=[];
for i in range(2,13)    :
    #%
    pin = board1.get_pin('d:' + `i` + ':s')
    pinlist_board1.append(pin)
    pin.write(43)
    pin = board2.get_pin('d:' + `i` + ':s')
    pinlist_board2.append(pin)
    pin.write(43)
#% move pins by list
#def moveall(dapin,a):
#    if a == 1:
#        degr=85;
#    elif dapin==2 or dapin==7:
#        degr=43;
#    else:
#        degr=43;    
#    pinlist_board1[dapin-1].write(degr)    # -2 fixes the factthat we start with pin 2, and python counts arrays starting with 0
def movealldegr(dapin,degr):
    # 28 degrees to close, 92 to open
    try:
        if dapin<7:
            pinlist_board1[dapin-1].write(degr)    # -1 fixes the factthat we start with pin 2, and python counts arrays starting with 0
        else:
            pinlist_board2[dapin-1-6].write(degr)    # -1 fixes the factthat we start with pin 2, and python counts arrays starting with 0
    except:
        pass
def logic2degree(door,logic): # translates open or close to degree of servo
    if logic==0:   # to close arm:
        degree = {  
            1: 70,
            2: 83,
            3: 76,
            4: 84,            
            5:115,
            6: 81,
            7:114,
            8: 93,
            9: 93,
            10:90,
            11:99,
            12:113,
            } 
    elif logic==1: # to open arm:
        degree = {  
            1: 24,
            2: 21,
            3: 14,
            4: 20,            
            5: 29,
            6: 10,
            7: 29 ,
            8: 25,
            9: 23,
            10:15,
            11:36,
            12:42,
            }                 
    return degree.get(door, "nothing")
#%%    
def moveall(door,openclose):
    try:
        if door==0 or door==999 :
            return
        flutter=5
        degree=logic2degree(door,openclose)
        movealldegr(door,degree-flutter) 
        t.sleep(.02)
        movealldegr(door,degree)     
        movealldegr(door,degree-flutter) 
        movealldegr(door,degree) 
    except:
        pass
def close_slowly(door)   :
    try:
        if door==0 or door==999 :
            return
        flutter=10
        print 'closing slowly door ', door
        degree_open=logic2degree(door,1)
        degree_clos=logic2degree(door,0)
    #    print degree_open
        #    print degree
    #    if degree_open-flutter<1:
    #        degree_open=1
        print door,degree_open,degree_clos,flutter
        print degree_open+flutter,degree_open-flutter
        movealldegr(door,degree_open+flutter) 
        t.sleep(.31)
        movealldegr(door,degree_clos-flutter)     
        t.sleep(.31)
        movealldegr(door,degree_clos) 				
    except:
        pass
def testdoor(idoor)    :
    while 1:
        moveall(idoor,1)
        t.sleep(1)
        moveall(idoor,0)
        t.sleep(1)
#testdoor(5)        
#%%
def closeall():
    for idoor in range(1,13):
        moveall(idoor,0)
def openall():
    for idoor in range(1,13):
        moveall(idoor,1)
#% test        
#for idoor in range(1,13):
#    close_slowly(idoor)
#for idoor in range(1,13):
#    moveall(idoor,0)    
#    moveall(idoor,1)    
#% functions for the sliders
def m1(degr):
    movealldegr(1,degr) 
def m2(degr):
    movealldegr(2,degr) 
def m3(degr):
    movealldegr(3,degr) 
def m4(degr):
    movealldegr(4,degr) 
def m5(degr):
    movealldegr(5,degr) 
def m6(degr):
    movealldegr(6,degr) 
def m7(degr):
    movealldegr(7,degr) 
def m8(degr):
    movealldegr(8,degr) 
def m9(degr):
    movealldegr(9,degr) 
def m10(degr):
    movealldegr(10,degr) 
def m11(degr):
    movealldegr(11,degr) 
def m12(degr):
    movealldegr(12,degr) 

#%% set up GUI
def argui():
    root=[];
    root = Tk()     
    #% draw a nice big slider for servo position
    scale1 = Scale(root,
        command = m1,
        to = 175,
        orient = HORIZONTAL,
        length = 800,
        label = 'Arm1')
    scale1.set(logic2degree(1,0))
    scale1.pack(anchor = CENTER)
    scale1 = Scale(root,
        command = m2,
        to = 175,
        orient = HORIZONTAL,
        length = 800,
        label = 'Arm2')
    scale1.set(logic2degree(2,0))
    scale1.pack(anchor = CENTER)
    scale1 = Scale(root,
        command = m3,
        to = 175,
        orient = HORIZONTAL,
        length = 800,
        label = 'Arm3')
    scale1.set(logic2degree(3,0))
    scale1.pack(anchor = CENTER)
    scale1 = Scale(root,
        command = m4,
        to = 175,
        orient = HORIZONTAL,
        length = 800,
        label = 'Arm4')
    scale1.set(logic2degree(4,0))
    scale1.pack(anchor = CENTER)
    scale1 = Scale(root,
        command = m5,
        to = 175,
        orient = HORIZONTAL,
        length = 800,
        label = 'Arm5')
    scale1.set(logic2degree(5,0))
    scale1.pack(anchor = CENTER)
    scale1 = Scale(root,
        command = m6,
        to = 175,
        orient = HORIZONTAL,
        length = 800,
        label = 'Arm6')
    scale1.set(logic2degree(6,0))
    scale1.pack(anchor = CENTER)
    scale1 = Scale(root,
        command = m7,
        to = 175,
        orient = HORIZONTAL,
        length = 800,
        label = 'Arm7')
    scale1.set(logic2degree(7,0))
    scale1.pack(anchor = CENTER)
    scale1 = Scale(root,
        command = m8,
        to = 175,
        orient = HORIZONTAL,
        length = 800,
        label = 'Arm8')
    scale1.set(logic2degree(8,0))
    scale1.pack(anchor = CENTER)    
    scale1 = Scale(root,
        command = m9,
        to = 175,
        orient = HORIZONTAL,
        length = 800,
        label = 'Arm9')
    scale1.set(logic2degree(9,0))
    scale1.pack(anchor = CENTER)
    scale1 = Scale(root,
        command = m10,
        to = 175,
        orient = HORIZONTAL,
        length = 800,
        label = 'Arm10')
    scale1.set(logic2degree(10,0))
    scale1.pack(anchor = CENTER)    
    scale1 = Scale(root,
        command = m11,
        to = 175,
        orient = HORIZONTAL,
        length = 800,
        label = 'Arm11')
    scale1.set(logic2degree(11,0))
    scale1.pack(anchor = CENTER)    
    scale1 = Scale(root,
        command = m12,
        to = 175,
        orient = HORIZONTAL,
        length = 800,
        label = 'Arm12')
    scale1.set(logic2degree(12,0))
    scale1.pack(anchor = CENTER)    
    
    def quit(root):
        root.destroy()
    Button(root, text="Quit", command=lambda root=root:quit(root)).pack()
    root.mainloop()
closeall()    



#%% start a background process with the main function

import threading, time, Queue, termios,sys,tty    
def argui_thread():
    global commands
    # setting a cross platform getch like function
    def getch() :
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try :
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally :
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    
    # this will allow us to communicate between the two threads
    # Queue is a FIFO list, the param is the size limit, 0 for infinite
    commands = Queue.Queue(0)
    
    # the thread reading the command from the user input     
    def control(commands) :
    
        while 1 :
    
            command = getch()
            commands.put(command) # put the command in the queue so the other thread can read it
    
            #  don't forget to quit here as well, or you will have memory leaks
            if command == "q" :
                break
    
    
    # your function displaying the words in an infinite loop
    def display(commands):
    
        #string = "the fox jumped over the lazy dog"
        #words = string.split(" ")
        pause = False 
        command = ""
    
        # we create an infinite generator from you list
        # much better than using indices
        #word_list = itertools.cycle(words) 
    
        # BTW, in Python itertools is your best friend
    
        while 1 :
    
            # parsing the command queue
            try:
               # false means "do not block the thread if the queue is empty"
               # a second parameter can set a millisecond time out
               command = commands.get(False) 
            except Queue.Empty:
               command = ""
    
            # behave according to the command
            if command == "q" :
                break
    
            if command == "p" :
                pause = True
    
            if command == "r" :
                pause = False
    
            # if pause is set to off, then print the word
            # your initial code, rewritten with a generator
            if not pause :
                #os.system("clear")
                #blink()
                mainfun()
                #print word_list.next() # getting the next item from the infinite generator 
    # then start the two threads
    displayer = threading.Thread(None, # always to None since the ThreadGroup class is not implemented yet
                                display, # the function the thread will run
                                None, # doo, don't remember and too lazy to look in the doc
                                (commands,), # *args to pass to the function
                                 {}) # **kwargs to pass to the function
    
    controler = threading.Thread(None, control, None, (commands,), {})
    #% start the threads
    displayer.start()
    controler.start()    
def stopthreads():
    global commands
    commands.put('q')
closeall()    
