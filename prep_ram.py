do_control_doors=1
import os
#%% prep video acquisition including template match for ends of arms (THIS USES WEBCAM, THEN DESTROYS that instance)
#from prep_video_no_kinect import *
execfile("./prep_video.py")

#%% =================================================================================================    
#%% ACTUAL BEHAVIORAL state machine programs:
def ram(total_narms=12,ndoors_to_open=12,closeall=[],openall=[],moveall=[],close_slowly=[],ntrials=1,ppal_stim=[],ppal_cam=[]):
    #%% INITIATE STUFF
    print "Starting maze behavioral program on ", total_narms, " arms and ", ndoors_to_open, " training doors"
    if trial>1:
        do_continue=input('Do another trial? 0 or 1')
        if do_continue==0: return
    do_stim=input('Do stimulation? 0=no, 1=training, 2=delay, 3=test') 
    stim_on=0
    timeout=20 # maximum minutes before trial is over
    if total_narms==ndoors_to_open:
        lendelay=0 # delay duration in seconds, default 60
    else:
        lendelay=60
    global state,trials,curcoord, arms_visited,doors_to_open,curnarm,doors_open,arms_to_visit,sample,daname,out_frame,didtimeout,arms_to_visit
    ram_should_continue=True
    arms_visited=[];arms_to_visit=[]; arms_visited=[];doors_to_open=[];curnarm=[];doors_open=[];trials=1;
    curcoord=(0,0);    state="0";    didtimeout=0;    arms_to_visit=(0,0)    
    print dista(curcoord,curcoord)#killme
    dict_writer=init_data_file(total_narms,ndoors_to_open,do_stim)
    #%% get filename, start oat record
    thefilename=get_filename_box()   
    ## OAT RECORD
    ## Save frame stream 'raw' and positional stream 'pos' 
#    os.system('  oat record -p pos            -d -f /home/m/usb/data/video/tracking/fall/ -n ' + thefilename + ' &  ')
#    os.system('  oat record -s view_pos_raw   -d -f /home/m/usb/data/video/movies/fall/   -n ' + thefilename + ' &  ')
    #% SOCKET TO COMMUNICATE WITH RAM
#    os.system('oat  posisock pub pos   tcp://127.0.0.1:5550 &')
#    os.system('oat  posisock pub kpos  tcp://127.0.0.1:5551 &')
    #%% 
    if do_control_doors and is_safe_to_control_doors(curcoord):
        closeall()
    # wait for the rat to get in, get keyboard input
    state='waiting_for_press_space'
    while state=='waiting_for_press_space':
        _=read_and_show()
        print2fig("Did you rebait? Min area at 50? Put in the rat, then press space...")
        user_input=cv2.waitKey(10)
        if ' ' == chr(user_input & 255):
            state="waiting_rat_to_center"
    ppal_cam(1)                
    datime=time.strftime("%d-%m-%Y--%H:%M:%S")
    daname='ramtest_'+datime + thefilename 
    print daname        
    #%% WAIT to get to center
    curcoord=(0,0);arms_visited=[]; curnarm=999;prevnarm=999; doors_to_open=[]; doors_open=[]; didtimeout=0; diderrors =[0,0] # initialize [train-phase-errors test-phase-errors]
    trial_starts = time.time()
    #% generate 4 rand integers from 1 to total narms to close those doors    
    doors_to_open=random.sample(range(1,total_narms+1), ndoors_to_open)#[randint(1,8) for p in range(0,4)]
    arms_to_visit=doors_to_open
    while state=="waiting_rat_to_center" and not ram_should_continue==False:
        if ram_should_continue==False:
            exit_nicely(ppal_cam); return  
        curnarm,curcoord,frame_and_info,sample,ram_should_continue=read_and_show(1,diderrors)
        if curnarm==0:
            state='Training'
            print state   
        write_data(arms_visited,diderrors,dict_writer,stim_on)
    #%% 1st set: open  random DOORS      
    if do_stim==1:
        ppal_stim(1);stim_on=1
    if do_control_doors :
        print('Opening 1st set of doors: ' +str(doors_to_open)) ;    print2fig('Opening 1st set of doors: ' +str(doors_to_open))    
        for door in doors_to_open:
            moveall(door,1) 
    arms_visited=[];    
    while state=='Training': # the trial has to be less than 5 mins:
        # Got terminate command from user?
        if ram_should_continue==False:
            exit_nicely(); break
        # Timeout?
        elapsed=time.time()-trial_starts          
        if elapsed>60*(timeout-1): # the trial has to be less than 5 mins:
            print 'Time ran out! Exiting';print2fig('Time ran out! Exiting');state='Timeout';  break
        if not (curnarm==999): 
            prevnarm=curnarm # save this arm to determine if the arm changed (he just entered this arm)
        # get current arm from oat:     
        curnarm,curcoord,frame_and_info,sample,ram_should_continue=read_and_show(1,diderrors)
        # sanity check:
        if (curnarm in doors_to_open) ==False and curnarm !=0 and curnarm !=999 :
            print2fig('Error: He can''t be in closed arm!!')
        # An incorrect or correct visit:         
        if is_near_feeder(curcoord,curnarm) and curnarm!=prevnarm and (curnarm!=999) and (curnarm!=0)  and (curnarm!=111):
            print "Entered arm " + str(curnarm)
            arms_visited.append(curnarm)
            if curnarm in arms_to_visit:
                # remove current arm from tovisit 
                print "This is a correct visit"
                arms_to_visit=list(set(range(1,total_narms+1))-set(arms_visited))#filter(lambda a: a != curnarm, arms_to_visit) # or in python3: list(filter((curnarm).__ne__, arms_to_visit))
            else:
                diderrors[0]+=1;
                print "This is an incorrect visit; diderrors = " +str(diderrors)
            print "Time: ", elapsed/60,'Visited: ',arms_visited; print 'Left: ',arms_to_visit
        #% CHECK IF DONE
        if contains(doors_to_open,arms_visited) and is_near_feeder(curcoord,curnarm): # move to next state
            state='wait_for_eating'                
            print '========================'
            print state,trials,arms_visited
        write_data(arms_visited,diderrors,dict_writer,stim_on)
    # Wait a few seconds to let him eat in peace    
    timestop=time.time()
    while state=='wait_for_eating':    
        curnarm,curcoord,frame_and_info,sample,ram_should_continue=read_and_show()
        if (time.time()-timestop)>1.5:
            state="wait_to_close_delay"
        write_data(arms_visited,diderrors,dict_writer,stim_on)
	#%% DELAY PHASE
    while state=="wait_to_close_delay":    
        curnarm,curcoord,frame_and_info,sample,ram_should_continue=read_and_show()
        if do_control_doors and is_safe_to_control_doors(curcoord) and not total_narms==ndoors_to_open :    
            closeall();        doors_open=0
            state="delay"
    if do_stim==1:
        ppal_stim(0);stim_on=0
    if do_stim==3:
        ppal_stim(1);stim_on=1

    while_starts = time.time()
    while state=='delay'  and elapsed<60*(timeout) and not doors_open==range(1,total_narms+1): # the trial has to be less than timeout:
        if round((time.time() -while_starts)/5) % 2 == 0:
            print("Waiting for {0} seconds out of lendelay".format(int(time.time() - while_starts))) 
        curnarm,curcoord,frame_and_info,sample,ram_should_continue=read_and_show(1,diderrors)
        if ram_should_continue==False:
            exit_nicely(); break
        if (time.time() -while_starts)>lendelay:
            state='wait_for_safe2open'
        write_data(arms_visited,diderrors,dict_writer,stim_on)
        
    #%% wait until it's safe to open arms (he is near feeder)
    doors_to_open=range(1,total_narms+1)
    timestop=time.time()
    while state=='wait_for_safe2open' and do_control_doors and total_narms!=ndoors_to_open :    
        curnarm,curcoord,frame_and_info,sample,ram_should_continue=read_and_show()
        if is_safe_to_control_doors(curcoord):
            print '2nd set of arms_to_visit is: ' + str(arms_to_visit);    print2fig('Opening 2nd set of doors: ' +str(doors_to_open))    
            openall(); doors_open=range(1,total_narms+1);
            state="Test"
        write_data(arms_visited,diderrors,dict_writer,stim_on)
    if do_stim==3:
        ppal_stim(0);stim_on=0
    if do_stim==2:
        ppal_stim(1);stim_on=1


	#%% TEST PHASE
    send_note(state)
    while state=='Test':
        # Got terminate command from user?
        if ram_should_continue==False:
            exit_nicely(); break
        # Timeout?
        elapsed=time.time()-trial_starts          
        if elapsed>60*(timeout-1): # the trial has to be less than 5 mins:
            print 'Time ran out! Exiting';print2fig('Time ran out! Exiting');state='Timeout';  break
        if not (curnarm==999): 
            prevnarm=curnarm # save this arm to determine if the arm changed (he just entered this arm)
        # get current arm from oat:     
        curnarm,curcoord,frame_and_info,sample,ram_should_continue=read_and_show(1,diderrors)
        # An incorrect or correct visit:         
        if is_near_feeder(curcoord,curnarm) and curnarm!=prevnarm and (curnarm!=999) and (curnarm!=0)  and (curnarm!=111):
            print "Entered arm " + str(curnarm)
            arms_visited.append(curnarm)
            if curnarm in arms_to_visit:
                # remove current arm from tovisit 
                print "This is a correct visit"
                arms_to_visit=list(set(range(1,total_narms+1))-set(arms_visited))#filter(lambda a: a != curnarm, arms_to_visit) # or in python3: list(filter((curnarm).__ne__, arms_to_visit))
                send_note("visited a correct arm in test phase")   
            else:
                diderrors[1]+=1;
                print "This is an incorrect visit; diderrors = " +str(diderrors)
            print "Time: ", elapsed/60,'Visited: ',arms_visited; print 'Left: ',arms_to_visit
             
        # Trial is over when:    
        if  contains(doors_to_open,arms_visited):
            curnarm,curcoord,frame_and_info,sample,ram_should_continue=read_and_show()
            lastarm=curnarm;lastdoor=armcoords[lastarm];
            state='wait_for_eatingtest'
            print state;            print2fig(state);            break
        write_data(arms_visited,diderrors,dict_writer,stim_on)
    
    # Wait a few seconds to let him eat in peace    
    timestop=time.time()
    while state=='wait_for_eatingtest':    
        curnarm,curcoord,frame_and_info,sample,ram_should_continue=read_and_show(1,diderrors)
        if (time.time()-timestop)>1.5:
            state="wait_for_safe2closelast"
        write_data(arms_visited,diderrors,dict_writer,stim_on)
    if do_stim==2:
        ppal_stim(0);stim_on=0

    # close all arms except current, to let him get to center:    
    print 'In arm ', curnarm, '; Will close ', range(1,curnarm) + range(curnarm+1,total_narms+1) 
    for door in range(1,curnarm) + range(curnarm+1,total_narms+1):
        print "closing arm " , door
        moveall(door,0) 
    
    while state=='wait_for_safe2closelast':    
        curnarm,curcoord,frame_and_info,sample,ram_should_continue=read_and_show(1,diderrors)
        if ram_should_continue==False:
            exit_nicely(); break
        print curnarm,dista(lastdoor,curcoord)
        if curnarm==0 and dista(lastdoor,curcoord)>50700 :#is_safe_to_control_doors(curcoord) and time.time()-timestop<4:
            print 'closing slowly',lastarm
            close_slowly(lastarm)
            state='Done!'
            print state;            print2fig(state);            break
        write_data(arms_visited,diderrors,dict_writer,stim_on)
    send_note("intertrial")   
    print 'saving ' + '/home/m/Dropbox/maze/'+daname+'.csv ...'
    #%% save data to disk
    sio.savemat('/home/m/usb/data/video/maze_control/fall/'+daname,{'d':d})
    f = open('/home/m/usb/data/video/maze_control/fall/'+daname+'_atend.csv', 'wb')    
    dict_writer = csv.DictWriter(f,keys)
    dict_writer.writer.writerow(keys)
    dict_writer.writerows(d)
    print 'saved'
    exit_nicely()
    print 'sleep';time.sleep(5);print 'out'
    

