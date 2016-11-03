do_control_doors=1
import os
#%% prep video acquisition including template match for ends of arms 
#from prep_video_no_kinect import *
execfile("./prep_video_gige.py")


#%% =================================================================================================    
#%% ACTUAL BEHAVIORAL state machine programs:
def ram(total_narms=12,ndoors_to_open=12,closeall=[],openall=[],moveall=[],close_slowly=[],ntrials=1,ppal_stim=[],ppal_cam=[]):
    #%% INITIATE 
    print "Starting maze behavioral program on ", total_narms, " arms and ", ndoors_to_open, " training doors"
    stim_on=0;lastarm=1;lastdoor=armcoords[lastarm]
    timeout=45 # maximum minutes before trial is over
    if total_narms==ndoors_to_open:
        lendelay=0 # delay duration in seconds, default 60
    else:
        lendelay=1*60  # in seconds
    print 'delay is ',lendelay, ' seconds'
    global state,trials,curcoord, arms_visited,doors_to_open,curnarm,doors_open,arms_to_visit,sample,daname,didtimeout,arms_to_visit
    curcoord=(0,0);arms_visited=[]; curnarm=999;prevnarm=999; doors_to_open=[]; doors_open=[]; didtimeout=0; diderrors =[0,0] # initialize [train-phase-errors test-phase-errors]
    Frame,frame_hd=read()
    ram_should_continue=True
    arms_visited=[];arms_to_visit=[]; arms_visited=[];doors_to_open=[];curnarm=[];doors_open=[];Curnarm=[];
    curcoord=(0,0);    state="0";    didtimeout=0;    arms_to_visit=(0,0) 
    if do_control_doors and is_safe_to_control_doors(curcoord):
        closeall()
    # wait for the rat to get in, get keyboard input
    state='waiting_for_press_space'
    print state
    #%% get filename, start oat record
    thefilename,trials,do_stim=get_filename_box()   
    dict_writer=init_data_file(total_narms,ndoors_to_open,do_stim,lendelay)    
    datime=time.strftime("%d-%m-%Y--%H:%M:%S")
    daname='ramtest_'+datime + thefilename 
    print daname        
    oat_connection_prep()
    ppal_cam(1)                
    print "do_stim = " , do_stim
    state="waiting_before_start"
    timestart=time.time()
    while state=='waiting_before_start':
        curnarm,curcoord,frame_and_info,sample,ram_should_continue,Curnarm=read_and_show(Frame)
        if (time.time()-timestart)>3:
            state="waiting_rat_to_center"
        write_data(arms_visited,diderrors,dict_writer,stim_on)
        
    #%% WAIT to get to center
    trial_starts = time.time()
    doors_to_open  = random.sample(range(1,total_narms+1), ndoors_to_open)#[randint(1,8) for p in range(0,4)]
    #%% generate 4 rand integers from 1 to total narms to close those doors    
    #    doors_for_test = list(set(range(1,total_narms+1))-set(doors_to_open))  
    #    while check_is_consecutive(doors_for_test) or (12 in doors_for_test and 1 in doors_for_test):
    #        print('Regenerating list due to presence of consecutive arms'+str(doors_for_test))
    #        doors_to_open=random.sample(range(1,total_narms+1), ndoors_to_open)#[randint(1,8) for p in range(0,4)]
    #        doors_for_test=list(set(range(1,total_narms+1))-set(doors_to_open))
    #%%    
    arms_to_visit=doors_to_open
    while state=="waiting_rat_to_center" and not ram_should_continue==False:
        if ram_should_continue==False:
            exit_nicely(ppal_cam); return  
        curnarm,curcoord,frame_and_info,sample,ram_should_continue,Curnarm=read_and_show(Frame,1,diderrors,'',Curnarm)
        if curnarm==0:
            state='Training'
            print state   
        write_data(arms_visited,diderrors,dict_writer,stim_on)
    #%% 1st set: open  random DOORS      
    if do_stim==1 :
        ppal_stim(1);stim_on=do_stim
    if do_control_doors :
        print('Opening 1st set of doors: ' +str(doors_to_open)) ;   
        print2fig(Frame,diderrors,'Opening 1st set of doors: ' +str(doors_to_open),Curnarm)    
        for door in doors_to_open:
            moveall(door,1) 
    arms_visited=[];    
    while state=='Training': # the trial has to be less than 5 mins:
        # Got terminate command from user?
        if ram_should_continue==False:
            exit_nicely(ppal_cam); break
        # Timeout?
        elapsed=time.time()-trial_starts          
        if elapsed>60*(timeout-1): # the trial has to be less than 5 mins:
            print 'Time ran out! Exiting';print2fig(Frame,diderrors,'Time ran out! Exiting',Curnarm);state='Timeout';  break
        if not (curnarm==999 or curnarm==0) : 
            prevnarm=curnarm # save this arm to determine if the arm changed (he just entered this arm)
        # get current arm from oat:     
        curnarm,curcoord,frame_and_info,sample,ram_should_continue,Curnarm=read_and_show(Frame,1,diderrors,'',Curnarm)
        # sanity check:
        if (curnarm in doors_to_open) ==False and curnarm !=0 and curnarm !=999 :
            print2fig(Frame,diderrors,'Error: He can''t be in closed arm!!',Curnarm)
        # An incorrect or correct visit:         
        if  curnarm!=prevnarm and (curnarm!=999) and (curnarm!=0)  and (curnarm!=111):
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
        curnarm,curcoord,frame_and_info,sample,ram_should_continue,Curnarm=read_and_show(Frame)
        if ram_should_continue==False: exit_nicely(ppal_cam); break
        if (time.time()-timestop)>1.5:
            state="wait_to_close_delay"
        write_data(arms_visited,diderrors,dict_writer,stim_on)
	#%% DELAY PHASE
    while state=="wait_to_close_delay":    
        curnarm,curcoord,frame_and_info,sample,ram_should_continue,Curnarm=read_and_show(Frame)
        if do_control_doors and is_safe_to_control_doors(curcoord) and not total_narms==ndoors_to_open :    
            closeall();        doors_open=0
            state="delay"
    
    if do_stim==1:
        ppal_stim(0);stim_on=0
    if do_stim==3:
        ppal_stim(1);stim_on=do_stim
            
    while_starts = time.time()
    cam_on=1;minutes_pause=5
    while state=='delay'  and elapsed<60*(timeout) and not doors_open==range(1,total_narms+1): # the trial has to be less than timeout:
        if lendelay > minutes_pause*60 and cam_on==1 and (time.time() -while_starts) > minutes_pause*60 and (time.time() -while_starts) < lendelay-minutes_pause*60:
            ppal_cam(0);cam_on=0 # turn camera off to avoid recording a lot of nothing
        if lendelay > minutes_pause*60 and cam_on==0 and (time.time() -while_starts) > lendelay-minutes_pause*60 :
            ppal_cam(1);cam_on=1 # turn camera back on
        if round(time.time() -while_starts) % 6 == 0: # print information
            print 'Waiting for ', int(time.time() - while_starts), ' seconds out of ', lendelay,cam_on
            if not cam_on: time.sleep(.1)
        if cam_on:
            curnarm,curcoord,frame_and_info,sample,ram_should_continue,Curnarm=read_and_show(Frame,1,diderrors,'',Curnarm)
            if ram_should_continue==False: exit_nicely(ppal_cam); break
            if (time.time() -while_starts)>lendelay:
                state='wait_for_safe2open'
            write_data(arms_visited,diderrors,dict_writer,stim_on)
    #%% wait until it's safe to open arms (he is near feeder)
    doors_to_open=range(1,total_narms+1)
    timestop=time.time()
    while state=='wait_for_safe2open' and do_control_doors and total_narms!=ndoors_to_open :    
        curnarm,curcoord,frame_and_info,sample,ram_should_continue,Curnarm=read_and_show(Frame)
        if ram_should_continue==False: exit_nicely(ppal_cam); break
        if is_safe_to_control_doors(curcoord):
            print '2nd set of arms_to_visit is: ' + str(arms_to_visit);    print2fig(Frame,diderrors,'Opening 2nd set of doors: ' +str(doors_to_open),Curnarm)    
            openall(); doors_open=range(1,total_narms+1);
            state="Test"
        write_data(arms_visited,diderrors,dict_writer,stim_on)
    
    if do_stim==3:        ppal_stim(0);stim_on=0
    if do_stim==2:        ppal_stim(1);stim_on=do_stim
        
	#%% TEST PHASE
    send_note(thefilename+str(diderrors)+state)
    while state=='Test':
        # Got terminate command from user?
        if ram_should_continue==False:
            exit_nicely(ppal_cam); break
        # Timeout?
        elapsed=time.time()-trial_starts          
        if elapsed>60*(timeout-1): # the trial has to be less than 5 mins:
            print 'Time ran out! Exiting';print2fig(Frame,diderrors,'Time ran out! Exiting',Curnarm);state='Timeout';  break
        if not (curnarm==999): 
            prevnarm=curnarm # save this arm to determine if the arm changed (he just entered this arm)
        # get current arm from oat:     
        curnarm,curcoord,frame_and_info,sample,ram_should_continue,Curnarm=read_and_show(Frame,1,diderrors,'',Curnarm)
        # An incorrect or correct visit:         
        if curnarm!=prevnarm and (curnarm!=999) and (curnarm!=0)  and (curnarm!=111):
            print "Entered arm " + str(curnarm)
            arms_visited.append(curnarm)
            if curnarm in arms_to_visit:
                # remove current arm from tovisit 
                print "This is a correct visit"
                arms_to_visit=list(set(range(1,total_narms+1))-set(arms_visited))#filter(lambda a: a != curnarm, arms_to_visit) # or in python3: list(filter((curnarm).__ne__, arms_to_visit))
                send_note(thefilename+str(diderrors)+"visited a correct arm in test phase")   
            else:
                diderrors[1]+=1;
                print "This is an incorrect visit; diderrors = " +str(diderrors)
            print "Time: ", elapsed/60,'Visited: ',arms_visited; print 'Left: ',arms_to_visit
        
        write_data(arms_visited,diderrors,dict_writer,stim_on)     
        # Trial is over when:    
        if  contains(doors_to_open,arms_visited):
            print 'this arm is ' , curnarm,'prev arm was ',prevnarm
            if not (curnarm==999 or curnarm==0):
                lastarm=curnarm
            else:
                lastarm=prevnarm
            print 'last arm was ' , lastarm
            lastdoor=armcoords[lastarm-1];
            #curnarm,curcoord,frame_and_info,sample,ram_should_continue=read_and_show() # this breaks the whole flow
            state='wait_for_eatingtest'
            print state;            print2fig(Frame,diderrors,state,Curnarm);            break
        
    # Wait a few seconds to let him eat in peace    
    timestop=time.time()
    while state=='wait_for_eatingtest':    
        curnarm,curcoord,frame_and_info,sample,ram_should_continue,Curnarm=read_and_show(Frame,1,diderrors,'',Curnarm)
        if ram_should_continue==False: exit_nicely(ppal_cam); break
        if (time.time()-timestop)>1.5:
            state="wait_for_safe2closelast"
        write_data(arms_visited,diderrors,dict_writer,stim_on)
        
    # close all arms except current, to let him get to center:    
    print 'In arm ', lastarm, '; Will close ', range(1,lastarm) + range(lastarm+1,total_narms+1) 
    for door in range(1,lastarm) + range(lastarm+1,total_narms+1):
        print "closing arm " , door
        moveall(door,0) 
    if do_stim==2:
        ppal_stim(0);stim_on=0
    while state=='wait_for_safe2closelast':    
        curnarm,curcoord,frame_and_info,sample,ram_should_continue,Curnarm=read_and_show(Frame,1,diderrors,'',Curnarm)
        if ram_should_continue==False:     exit_nicely(ppal_cam); break
        print curnarm,dista(lastdoor,curcoord), curcoord
        if curnarm==0 and curcoord!=(0,0) and dista(lastdoor,curcoord)> 950000:#is_safe_to_control_doors(curcoord) and time.time()-timestop<4:
            print 'closing slowly',lastarm
            close_slowly(lastarm)
            state='Done!'
            print state;            print2fig(Frame,diderrors,state,Curnarm);            break
        write_data(arms_visited,diderrors,dict_writer,stim_on)
    send_note(thefilename+str(diderrors)+"intertrial")   
    exit_nicely(ppal_cam);
    print "out at",time.strftime("%H:%M:%S")
