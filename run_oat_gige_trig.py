import sys, os, time


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
except OSError:
    warnings.warn('No PulsePal found on /dev/ttyACM0!')
    
#%% Puilse Pal def      
def ppal_cam(control):
    if control==1:
        print 'Starting camera trigger...'
        #% start Trigger
        myPulsePal.programOutputChannelParam('customTrainID',      3, 0) 
        myPulsePal.programOutputChannelParam('phase1Voltage',      3, 5)
        myPulsePal.programOutputChannelParam('burstDuration' ,     3, 0) 
        myPulsePal.programOutputChannelParam('interBurstInterval', 3, 0) 
        myPulsePal.programOutputChannelParam('pulseTrainDelay',    3, 0) 
        myPulsePal.programOutputChannelParam('interPulseInterval', 3, .001) # time between stims (.05=20Hz but in practice used .005. Finally, use .001). This only has effect in trig mode 14!
        myPulsePal.programOutputChannelParam('phase1Duration',     3, .001) # duration of each stim 
        myPulsePal.programOutputChannelParam('pulseTrainDuration', 3, 90200) # How long to stim   
        myPulsePal.syncAllParams()
        myPulsePal.triggerOutputChannels(0, 0, 1, 0) # Soft-trigger channel
    elif control==0:
        #% Trigger off
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

        
do_detect=False
do_record=True
ppal_cam(0);

time.sleep(.3)
os.system('oat kill;oat clean  -q gpos graw gfilt gfilth gfilt gfilth gpos graw gview_raw gfilt_hsv graw gpos gview_raw gkpos gview_pos gfilt gfilt_bw gpreraw graw_dec gfilt_hsv gview_raw graw  view_raw gfilt_hsv graw gpos gview_raw gkpos gview_pos gfilt gfilt_bw gpreraw graw_dec groi gdec')


status=9
while status!=0:
    print 'Trying to start gige oat-frameserve'
    os.system('oat frameserve gige gpreraw  -c ~/Dropbox/bash/configs/oat/config_gige.toml frameserve-trig  &')
    time.sleep(4.5)
    status=os.WEXITSTATUS(os.system('killall -0 oat-frameserve'))  # check if frameserve is running

os.system('oat buffer    frame   gpreraw  graw &')


if do_detect is False and do_record is False:
    os.system('oat decorate    gpreraw gview_pos -s -t    &');
    os.system('oat view frame gview_pos -r 7 &')
else:
    os.system(' oat framefilt mask graw groi -c  ~/Dropbox/bash/configs/oat/config_gige.toml mask &  ') 
    os.system('oat framefilt bsub    groi     gfilt   -c ~/Dropbox/bash/configs/oat/config_gige.toml bg_config_LE   &')

    #os.system('oat framefilt col     gfilt    gfilth -C HSV & oat posidet hsv gfilth gpos  -c ~/Dropbox/bash/configs/oat/config_gige.toml hsv_config_LE  &')


    os.system('oat framefilt col  gfilt   gfilt_bw -C GREY    & oat posidet   thresh gfilt_bw gpos    -c ~/Dropbox/bash/configs/oat/config_gige.toml filt-thr-LE   &') # --tune

    #os.system(' oat posifilt kalman  gpos      gkpos      &  ') # kalman doesnt work for some reaseon

    #os.system('oat decorate    groi gview_pos  -p gkpos -p gpos -h  -s  -t    &'); ## SLOW
    #os.system('oat view frame gview_pos -r 8 &')
    os.system('oat view frame graw -r 8 &')
        
    os.system('oat  posisock pub gpos   -e tcp://127.0.0.1:5550 &')
    #os.system('oat  posisock pub gkpos  -e tcp://127.0.0.1:5551 &') # rep or pub (pub is asynchronous)


    
if do_record:
    os.system('oat record  -p gpos        -d -f /home/m/data/video/tracking/ -n rat_gige &')
    os.system('oat record -s  graw   -d -f /home/m/hdd/data/video/movies/   -n rat_gige -F MJPG   &') # H264 t<oo slow, MJPG better


ppal_cam(1)
