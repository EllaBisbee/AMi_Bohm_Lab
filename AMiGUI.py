import serial, tkinter as tk
from time import sleep
from datetime import datetime
from shutil import copyfile
from picamera import PiCamera
import numpy as np, RPi.GPIO as GPIO
import re, sys, os

camera_delay=.2 # delay, in seconds, that the system should sit idle before each image 
fracbelow=0.5 # this is the fraction of zrange below the expected plane of focus
xmax,ymax,zmax=160.,118.,29.3 #translation limits in mm  
disable_hard_limits=True  #this disables hard limits during RUN only
samp=0  #samp is the sub-sample index (used when there is more than one sample at each position)
samp_coord=[] #fractional coordinates of the individual samples 
gx,gy=0,0      #clicked coordinates on the canvas
mx,my,mz=0,0,0 #machine position
yrow,xcol=0,0  #sample position indices (starting at 0, not 1)
pose_txt='A1'   
corner='unset'
alphabet=''; nroot=''; sID=''
fname='AMi.config'
viewing=False; running=False; stopit=False
lighting1=False;lighting2=False
Ualphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ'; Lalphabet='abcdefghijklmnopqrstuvwxyz'
alphabet=[]

print('\n Bonjour, ami \n')
if not os.path.isdir("images"): # check to be sure images directory exists
   print( "\"images\" directory (or symbolic link) not found. \n This should be in the same directory as this program. \n You need to create the directory or fix the link before continuing. \n i.e. mkdir images")
   sys.exit()

def read_config():  # read information from the configuration file
    global tl,tr,bl,br,nx,ny,samps,zstep,nimages,nroot,sID,filee,alphabet,samp_coord
    try:
        f=open(fname,'r')
        jnk=list(map(int,(re.findall(r'\S+', (f.readline()).split('#', 1)[0]))))
        nx=jnk[0]; ny=jnk[1]; samps=jnk[2]
        tl=np.array(list(map(float,(re.findall(r'\S+', (f.readline()).split('#', 1)[0])))))
        tr=np.array(list(map(float,(re.findall(r'\S+', (f.readline()).split('#', 1)[0])))))
        bl=np.array(list(map(float,(re.findall(r'\S+', (f.readline()).split('#', 1)[0])))))
        br=np.array(list(map(float,(re.findall(r'\S+', (f.readline()).split('#', 1)[0])))))
        samp_coord=[]
        for i in range(samps):
            samp_coord.append(list(map(float,(re.findall(r'\S+',f.readline().split('#', 1)[0])))))
        zstep=float((f.readline()).split('#', 1)[0])
        nimages=int((f.readline()).split('#', 1)[0])
        sID=(f.readline()).split('#', 1)[0]
        sID=sID.replace("\n",""); sID=sID.replace(" ","")
        nroot=(f.readline()).split('#', 1)[0]
        nroot=nroot.replace("\n",""); nroot=nroot.replace(" ","")
        alphabet=Ualphabet[0:ny]+Lalphabet[0:ny]
    except:
        print(' The configuration file was missing or the format was not right. It should look something like this:')
        print('  12   8    1        # number of positions along x and y and on the plate then number of samples at each position') 
        print('  134.2  29.3  7.5   # coordinates of the top left drop')
        print('   35.2  28.7  7.3   # coordinates of the top right drop')
        print('  133.5  92.9  7.1   # coordinates of the bottom left drop')
        print('   35.0  91.9  7.0   # coordinates of the bottom right drop')
        print('    0.    0.         # offsets for each sample (first sample is always 0. 0.)')
        print('   0.3               # image spacing in z')
        print('   4                 # number of images per drop')
        print('   AMi_sample        # sample name (no spaces)')
        print('   AB_xs2            # plate name (no spaces)')
        print('File error.')
        f.close()
        if fname=='AMi.config': sys.exit()
read_config()

# camera setup
camera = PiCamera()
camera.resolution=(1640,1232)
camera.iso=50 # nnot sure this does anytihng

#light1 and light2 setup - this is controled by gpio pins 17 and 18 on the pi
#the light2 button also controls the 24V output of the arduino
#gpio 27 is used to tell the pi when the arduino has fininished moving
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17,GPIO.OUT) #controls light 1
GPIO.setup(18,GPIO.OUT) #controls light 2
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # signal for movement completion


def tdate(): # get the current date as a nice string
   dstr=(datetime.now().strftime('%h-%d-%Y_%I:%M%p')) 
   dstr=dstr.replace(" ","")
   return dstr

def wait_for_Idle(): # wait for grbl to complete movement -new version wait for pin A8 to go low 
   s.write(('m9 \n').encode('utf-8')) # set pin A3 low
#   print('sending m9') #set A8 low 
   sleep(0.2) #wait a little just in case
   while GPIO.input(27):
#      print('waiting...') 
      sleep(0.1)
   s.write(('m8 \n').encode('utf-8')) # set pin A3 high 
#   print('our long wait has ended')
   
# connect to the arduino and set zero 
s = serial.Serial('/dev/ttyUSB0',115200) # open grbl serial port
s.write(("\r\n\r\n").encode('utf-8')) # Wake up grbl
sleep(2)   # Wait for grbl to initialize
s.flushInput()  # Flush startup text in serial input
s.write(('$21=1 \n').encode('utf-8')) # enable hard limits
print(' ok so far...')
s.write(('$H \n').encode('utf-8')) # tell grbl to find zero 
grbl_out = s.readline() # Wait for grbl response with carriage return
s.write(('? \n').encode('utf-8')) # Send g-code block to grbl
response = s.readline().decode('utf-8') # Wait for grbl response with carriage return
response=response.replace(":",","); response=response.replace(">",""); response=response.replace("<","")
a_list=response.split(",")
#print(a_list)
wx=float(a_list[6]); wy=float(a_list[7]); wz=float(a_list[8])
if wx==-199.0:
  s.write(('G10 L2 P1 X '+str(wx)+' Y '+str(wy)+' Z '+str(wz)+' \n').encode('utf-8')) # ensures that zero is zero and not -199.0, -199.0, -199.0 
  grbl_out = s.readline() # Wait for grbl response with carriage return
s.write(('m8 \n').encode('utf-8')) # set pin A3 high -used later to detect end of movement 
print(' You\'ll probably want to click VIEW and turn on some lights at this point. \n Then you may want to check the alignment of the four corner samples')
s.write(('$x \n').encode('utf-8')) # unlock so spindle power can engage for light2 
grbl_out = s.readline() # Wait for grbl response with carriage return
s.write(('s1000 \n').encode('utf-8')) # set max spindle volocity
grbl_out = s.readline() # Wait for grbl response with carriage return
             
def update_b(event): # write parameters to the configuration file
    global tl,tr,bl,br,nx,ny,zstep,nimages,nroot,sID,filee,fname,alphabet,samps
    write_b()

def write_b():
    fname=str(filee.get())
    if " " in fname: 
        canvas.create_rectangle(2,2,318,60,fill='white')
        canvas.create_text(160,35,text=('file name cannot contain spaces. Nothing written.'))
        filee.delete(0,tk.END); filee.insert(0,""); canas.update()
    else:
         f=open(fname,'w')
         nx=int(nxe.get())
         ny=int(nye.get())
         samps=int(sampse.get())
         nimages=int(nimge.get())
         zstep=float(zspe.get())
         sID=str(sIDe.get())
         nroot=str(IDe.get())
         f.write(str('%6d%6d%6d     # number of positons on x and y, then the number of samples at each position\n'%(nx,ny,samps)))
         f.write(str('%9.3f%9.3f%9.3f  # coordinates of the top left sample\n'%(tl[0],tl[1],tl[2])))
         f.write(str('%9.3f%9.3f%9.3f  # coordinates of the top right sample\n'%(tr[0],tr[1],tr[2])))
         f.write(str('%9.3f%9.3f%9.3f  # coordinates of the bottom left sample\n'%(bl[0],bl[1],bl[2])))
         f.write(str('%9.3f%9.3f%9.3f  # coordinates of the bottom right sample\n'%(br[0],br[1],br[2])))
         for i in range(samps):
             try: test=samp_coord[i]
             except: samp_coord.append([0., 0.])
             ta=float(samp_coord[i][0])
             tb=float(samp_coord[i][1])
             f.write(str('%9.4f%9.4f  # fractional offsets of sub-sample \n'%(ta,tb)))
         f.write(str('%9.3f # zstep - the spacing in z between images\n'%(zstep)))
         f.write(str('%6d     # nimages - the number of images of each sample\n'%(nimages)))
         f.write(sID+'     # sample name\n')
         f.write(nroot+'     # plate name\n')
         f.close()
         canvas.create_rectangle(2,2,318,60,fill='white')
         canvas.create_text(160,35,text=('parameters saved to '+fname))

def read_b(event): #read parameters from specified configuration file 
    global tl,tr,bl,br,nx,ny,zstep,nimages,nroot,filee,fname,alphabet 
    fname=str(filee.get())
    read_config()
    filee.delete(0,tk.END); filee.insert(0,fname)
    nxe.delete(0,tk.END); nxe.insert(0,nx)
    nye.delete(0,tk.END); nye.insert(0,ny)
    nimge.delete(0,tk.END); nimge.insert(0,nimages)
    zspe.delete(0,tk.END); zspe.insert(0,zstep)
    sIDe.delete(0,tk.END); sIDe.insert(0,sID)
    IDe.delete(0,tk.END); IDe.insert(0,nroot)
    sampse.delete(0,tk.END); sampse.insert(0,samps)
    print('Parameters read from '+fname)
    canvas.update()

def mcoords(): # moves to the position specified by xcol, yrow
    global mx,my,mz
    print('called mcoords with yrow,xcol,samp:',yrow,xcol,samp)
    wait_for_Idle()
    x=xcol/float(nx-1)+samp_coord[samp][0]
    y=yrow/float(ny-1)+samp_coord[samp][1]
    mx=br[0]*x*y+bl[0]*(1.-x)*y+tr[0]*x*(1.-y)+tl[0]*(1.-x)*(1.-y)
    my=br[1]*x*y+bl[1]*(1.-x)*y+tr[1]*x*(1.-y)+tl[1]*(1.-x)*(1.-y)
    mz=br[2]*x*y+bl[2]*(1.-x)*y+tr[2]*x*(1.-y)+tl[2]*(1.-x)*(1.-y)
    print('mx,my,mz',mx,my,mz)
    s.write(('G0 x '+str(mx)+' y '+str(my)+' z '+ str(mz) + ' \n').encode('utf-8')) # g-code to grbl
    sleep(0.2)
    grbl_out = s.readline() # Wait for grbl response with carriage return
    letnum=alphabet[yrow]+str(xcol+1)
    if samps>1:letnum+=Lalphabet[samp]
    pose.delete(0,tk.END); pose.insert(0,letnum)
    wait_for_Idle()
    canvas.create_rectangle(2,2,318,60,fill='white')
    canvas.create_text(160,20,text=("showing "+letnum+'  position '+str(yrow*nx+xcol+1)),font="helvetica 11")
    canvas.create_text(160,39,text=('machine coordinates:  '+str(round(mx,3))+',  '+str(round(my,3))+',  '+str(round(mz,3))),font="helvetica 9",fill="grey")
    canvas.update()

def motion(event):
    global gx,gy,mx,my,mz
    gx, gy = event.x, event.y

def left_click(event):
    global gx,gy,corner,tl,tr,bl,br,pose,corner,alphabet,mx,my,mz,yrow,xcol,samps
    print('left_click gx,gy,xcol,yrow',gx,gy,xcol,yrow)

    #adjust z
    if gx<40 and gy<335 and gy>65 :
        rz=200-gy
        mzsav=mz
        mz+= 0.0001*(abs(rz)**2.2)*np.sign(rz)
        if mz>0. and mz<zmax:
            s.write(('G0 z'+ str(mz) + '\n').encode('utf-8')) # Send g-code block to grbl
            grbl_out = s.readline() # Wait for grbl response with carriage return
            if corner != 'unset':
                canvas.create_rectangle(5,35,315,57,fill='white',outline='white')
                canvas.create_text(160,47,text='current Z: '+str(round(mz,3))+' change: '+str(round((mz-mzsav),3)),font="Helvetia 9")
            print('current Z: '+str(round(mz,3))+' change: '+str(round((mz-mzsav),3)))
        else:
           canvas.create_rectangle(2,2,318,60,fill='white')
           canvas.create_text(160,27,text="that move would take you out of bounds",font="Helvetia 9")
           mz=mzsav
        canvas.update()

    #adjust xy
    elif gx>45 and gy<335 and gy>65: 
        rx,ry=gx-180,200-gy
        mxsav,mysav=mx,my
        mx+= 0.0001*(abs(rx)**2.2)*np.sign(rx)
        my+= 0.0001*(abs(ry)**2.2)*np.sign(ry)
        if mx>0. and my>0. and mx<xmax and my<ymax:
           s.write(('G0 x'+ str(mx) + ' y ' + str(my) +'\n').encode('utf-8')) 
           grbl_out = s.readline() # Wait for grbl response with carriage return
           if corner != 'unset':
              canvas.create_rectangle(5,35,315,57,fill='white',outline='white')
              canvas.create_text(160,47,text='current X,Y: '+str(round(mx,3))+', '+str(round((my),3)),font="Helvetia 9")
           print('current X: '+str(round(mx,3))+' change: '+str(round((mx-mxsav),3)))
           print('current Y: '+str(round(my,3))+' change: '+str(round((my-mysav),3)))
        else:
           canvas.create_rectangle(2,2,318,60,fill='white')
           canvas.create_text(160,27,text="that move would take you out of bounds",font="Helvetia 9")
           mx,my=mxsav,mysav
        canvas.update()

def tl_left_b(event):
         global xcol,yrow,samp,mx,my,mz,corner
         corner='TL'
         xcol=0; yrow=0; samp=0
         mcoords() # move to TL
         canvas.create_rectangle(2,2,318,60,fill='white')
         canvas.create_text(160,20,text="SET now changes TL coordinates",font="Helvetia 9")
         if samps>1:
             canvas.create_text(160,40,text="After the corners Right Click TL for sub-samples",font="Helvetia 9")

def tl_right_b(event):
         global xcol,yrow,samp,mx,my,mz,corner,samps,samp_coord
         samps=int(sampse.get())
         for i in range(samps): 
             try: test=samp_coord[i]
             except: samp_coord.append([0., 0.])
         print('samp_coord',samp_coord)
         if samps>1:
            samp+=1
            if samp==samps:samp=1
            corner=str(samp)
            xcol=0; yrow=0
            mcoords() # move to TL and indicated sample
            canvas.create_rectangle(2,2,318,60,fill='white')
            canvas.create_text(160,27,text="SET now changes sub-sample "+Lalphabet[samp]+" coordinates.",font="Helvetia 9")
         else:
            canvas.create_rectangle(2,2,318,60,fill='white')
            canvas.create_text(160,27,text="no sub-samples specified.",font="Helvetia 9")

def tr_b(event):
         global xcol,yrow,samp,mx,my,mz,corner
         corner='TR'
         xcol=nx-1; yrow=0; samp=0
         mcoords() # move to TR
         canvas.create_rectangle(2,2,318,60,fill='white')
         canvas.create_text(160,27,text="SET now changes TR coordinates",font="Helvetia 9")

def bl_b(event):
         global xcol,yrow,samp,mx,my,mz,corner
         corner='BL'
         xcol=0; yrow=ny-1; samp=0
         mcoords() # move to BL
         canvas.create_rectangle(2,2,318,60,fill='white')
         canvas.create_text(160,27,text="SET now changes BL coordinates",font="Helvetia 9")

def br_b(event):
         global xcol,yrow,samp,mx,my,mz,corner
         corner='BR'
         xcol=nx-1; yrow=ny-1; samp=0
         mcoords() # move to BR 
         canvas.create_rectangle(2,2,318,60,fill='white')
         canvas.create_text(160,27,text="SET now changes BR coordinates",font="Helvetia 9")

def set_b(event):
          global tl,tr,bl,br,mx,my,mz,xcol,yrow,corner
          m=[mx,my,mz]
          if corner=="TL":
             tl=m
             print('new tl',tl)
          if corner=="TR":
             tr=m
             print('new tr',tr)
          if corner=="BL":
             bl=m
             print('new bl',bl)
          if corner=="BR":
             br=m
             print('new br',br)
          if corner.isdigit():
             samp_coord[(int(corner))][0]=(m[0]-tl[0])/(tr[0]-tl[0])
             samp_coord[(int(corner))][1]=(m[1]-tl[1])/(bl[1]-tl[1])
             print('new sample '+corner+' coordinates: '+str(samp_coord[(int(corner))]))
          canvas.create_rectangle(2,2,318,60,fill='white')
          if corner=='unset':canvas.create_text(160,27,text=("You must first select a corner"),font="Helvetia 10")
          else:
              if corner.isdigit(): canvas.create_text(160,27,text=(Lalphabet[int(corner)]+" coordinates saved"),font="Helvetia 10")
              else: canvas.create_text(160,27,text=(corner + " coordinates saved"),font="Helvetia 10")
          corner='unset'
          canvas.update()

def view_b(event):
      global viewing
      canvas.create_rectangle(2,2,318,60,fill='white')
      if not running:
         if viewing: 
             camera.stop_preview()
             viewing=False
             canvas.create_text(160,27,text=("click VIEW to open live view"),font="Helvetia 10")
         else:
             camera.start_preview(fullscreen=False,window=(0,-76,1597,1200))
             viewing=True
             canvas.create_text(160,27,text=("click VIEW to close live view"),font="Helvetia 10")

def reset_b(event):
         global corner
         corner="unset"
         print('clicked origin reset')
         canvas.create_rectangle(2,2,318,60,fill='white')
         canvas.create_text(160,27,text=("wait while machine resets..."),font="Helvetia 10")
         canvas.update()
         s.write(('$X \n').encode('utf-8')) # Send g-code home command to grbl
         grbl_out = s.readline() # Wait for grbl response with carriage return
         s.write(('$H \n').encode('utf-8')) # Send g-code home command to grbl
         grbl_out = s.readline() # Wait for grbl response with carriage return
         canvas.create_rectangle(2,2,318,60,fill='white')
         canvas.create_text(160,27,text=("Ready to rumble!"),font="Helvetia 10")
         canvas.update()

def reset_br(event):
         global corner
         corner="unset"
         print('clicked reset alarm')
         canvas.create_rectangle(2,2,318,60,fill='white')
         canvas.create_text(160,27,text=("$X sent to GRBL..."),font="Helvetia 10")
         canvas.update()
         s.write(('$X \n').encode('utf-8')) # Send g-code home command to grbl
         grbl_out = s.readline() # Wait for grbl response with carriage return
         canvas.create_rectangle(2,2,318,60,fill='white')
         canvas.create_text(160,27,text=("It might work now..."),font="Helvetia 10")
         canvas.update()

def close_b(event): # Closes the interface if not collecting images.  Stops the run if you are collecting data.
    global stopit
    if running:
       print('stopping the run')
       stopit=True; 
    else:
       print('moving back to the origin and closing the graphical user interface')
       s.write(('$H \n').encode('utf-8')) # tell grbl to find zero 
       grbl_out = s.readline() # Wait for grbl response with carriage return
       root.quit()

def snap_b(event): # takes a simple snapshot of the current view
         global nroot
         sID=str(sIDe.get())
         nroot=str(IDe.get())
         path1='images/'+sID
         if not os.path.isdir(path1):
           os.mkdir(path1)
           print('created directory '+sID+' within the images directory')
         path1='images/'+sID+'/'+nroot
         if not os.path.isdir(path1):
           os.mkdir(path1)
           print('created directory '+nroot+' within the images/'+sID+' directory')
         path1=path1+'/snaps'
         if not os.path.isdir(path1):
           os.mkdir(path1)
           print('created directory \'snaps\' within the images/'+sID+'/'+nroot+' directory')
         if samps==1: 
             sname='images/'+sID+'/'+nroot+'/snaps/'+alphabet[yrow]+str(xcol+1)+"_"+tdate()+'.jpg'
         else: 
             sname='images/'+sID+'/'+nroot+'/snaps/'+alphabet[yrow]+str(xcol+1)+Lalphabet[samp]+"_"+tdate()+'.jpg'
         camera.capture(sname)
         canvas.create_rectangle(2,2,318,60,fill='white')
         canvas.create_text(160,17,text=('image saved to '+sname),font="Helvetia 10")
         canvas.update()

def snap_br(event): #right mouse snap - takes a series of z-stacked pictures using nimages and Z-spacing parameters
         global nroot,mx,my,mz
         sID=str(sIDe.get())
         nroot=str(IDe.get())
         nimages=int(nimge.get())
         zstep=float(zspe.get())
         samp_name=alphabet[yrow]+str(xcol+1)
         if samps>1:samp_name+=Lalphabet[samp]
         path1='images/'+sID
         if not os.path.isdir(path1):
           os.mkdir(path1)
           print('created directory '+sID+' within the images directory')
         path1='images/'+sID+'/'+nroot
         if not os.path.isdir(path1):
           os.mkdir(path1)
           print('created directory '+nroot+' within the images/'+sID+' directory')
         path1=path1+'/snaps'
         if not os.path.isdir(path1):
           os.mkdir(path1)
           print('created directory \'snaps\' within the images/'+sID+'/'+nroot+' directory')
         processf=open(path1+'/'+samp_name+'_process_snap.com','w')
         processf.write('rm OUT*.tif \n')
         zrange=(nimages-1)*zstep
         z=mz-(1-fracbelow)*zrange # bottom of the zrange (this is the top of the sample!)
         z_sav=mz
         processf.write('echo \'processing: '+samp_name+'\' \n')
         samp_name+='_'+tdate()
         line='align_image_stack -m -a OUT '
         for imgnum in range(nimages):
             s.write(('G0 z '+ str(z) + '\n').encode('utf-8')) # move to z
             grbl_out=s.readline()
             wait_for_Idle()
             imgname=path1+'/'+samp_name+'_'+str(imgnum)+'.jpg'
             sleep(camera_delay)#slow things down to allow camera to settle down
             camera.capture(imgname)
             line+=samp_name+'_'+str(imgnum)+'.jpg '
             z+=zstep
         line+=(' \n') 
         processf.write(line)
         processf.write('enfuse --exposure-weight=0 --saturation-weight=0 --contrast-weight=1 --hard-mask --output='+samp_name+'.tif OUT*.tif \n')
         processf.write('rm OUT*.tif \n')
         processf.close()
         s.write(('G0 z '+ str(z_sav) + '\n').encode('utf-8')) # return to original z 
         grbl_out=s.readline()
         wait_for_Idle()
         canvas.create_rectangle(2,2,318,60,fill='white')
         canvas.create_text(160,17,text=('individual images:'+path1),font="Helvetia 10")
         canvas.create_text(160,37,text=('source '+samp_name+'_process_snap.com to combine z-stack'),font="Helvetia 10")
         canvas.update()

def light1_b(event):
         global lighting1
         if lighting1: # light1 is on so we turn it off
             GPIO.output(17,GPIO.LOW)
             print('light1 turned off')
             lighting1=False
         else: # light1 is off so we turn it on
             GPIO.output(17,GPIO.HIGH)
             print('light1 turned on')
             lighting1=True

def light2_b(event): # this controls both the lower 120V AC output and the 24V DC output of the arduino 
         global lighting2
         if lighting2: # light2 is on so we turn it off
             GPIO.output(18,GPIO.LOW) # make pin 18 on the pi low
             s.write(('m5 \n').encode('utf-8')) #turn off the spindle power
             grbl_out = s.readline() # Wait for grbl response with carriage return
             print('light2 turned off')
             lighting2=False
         else: # light2 is off so we turn it on
             GPIO.output(18,GPIO.HIGH) # make pin 18 on the pi high
             s.write(('m3 \n').encode('utf-8')) #turn on spindle power
             grbl_out = s.readline() # Wait for grbl response with carriage return
             print('light2 turned on')
             lighting2=True

def run_b(event):
         global yrow,xcol,samp,mx,my,mz,corner,running,viewing,lighting1,lighting2,nroot,sID,nimages,zstep,samps,stopit
         write_b() # get data from the GUI window and save/update the configuration file... 
         nimages=int(nimge.get())
         samps=int(sampse.get()) 
         zstep=float(zspe.get()) 
         sID=str(sIDe.get())
         nroot=str(IDe.get())
         yrow=0; xcol=0; samp=0
         mcoords() #go to A1 
         imgpath='images/'+sID
         if not os.path.isdir(imgpath):
           os.mkdir(imgpath)
           print('created directory: '+imgpath)
         imgpath='images/'+sID+'/'+nroot
         if not os.path.isdir(imgpath):
           os.mkdir(imgpath)
           print('created directory: '+imgpath)
         imgpath+='/'+tdate()
         if not os.path.isdir(imgpath):
           os.mkdir(imgpath)
           print('created directory: '+imgpath)
         if not os.path.isdir(imgpath+'/rawimages'):
           os.mkdir(imgpath+'/rawimages')
           print('created directory: '+imgpath+'/rawimages')
           copyfile(fname,(imgpath+'/'+fname))
         if not viewing: 
             camera.start_preview(fullscreen=False,window=(0,-76,1597,1200))
             viewing=True
             sleep(2) # let camera adapt to the light before collecting images
         processf=open(imgpath+'/process'+nroot+'.com','w')
         processf.write('rm OUT*.tif \n')
         zrange=(nimages-1)*zstep
         running=True
         canvas.create_rectangle(2,2,318,60,fill='white')
         canvas.create_text(160,27,text=("imaging samples..."),font="Helvetia 10")
         canvas.update()
         if disable_hard_limits: 
           s.write(('$21=0 \n').encode('utf-8')) #turn off hard limits
           print('hard limits disabled')
         for yrow in range(ny):
            for xcol in range(nx):
                for samp in range(samps):  
                   mcoords() # go to the expected position of the focussed sample 
                   z=mz-(1-fracbelow)*zrange # bottom of the zrange (this is the top of the sample!)
                   samp_name=alphabet[yrow]+str(xcol+1)
                   if samps>1:samp_name+=Lalphabet[samp]
                   processf.write('echo \'processing: '+samp_name+'\' \n')
                   line='align_image_stack -m -a OUT '
                   for imgnum in range(nimages):
                      s.write(('G0 z '+ str(z) + '\n').encode('utf-8')) # move to z
                      grbl_out=s.readline()
                      wait_for_Idle()
                      sleep(0.2)
                      # take image
                      imgname=imgpath+'/rawimages/'+samp_name+'_'+str(imgnum)+'.jpg'
                      sleep(camera_delay)#slow things down to allow camera to settle down
                      camera.capture(imgname)
                      line+='rawimages/'+samp_name+'_'+str(imgnum)+'.jpg '
                      z+=zstep
                   line+=(' \n') 
                   processf.write(line)
                   processf.write('enfuse --exposure-weight=0 --saturation-weight=0 --contrast-weight=1 --hard-mask --output='+samp_name+'.tif OUT*.tif \n')
                   processf.write('rm OUT*.tif \n')
                   if stopit: break
                if stopit: break
            if stopit: break
         running=False
         processf.close()
         camera.stop_preview() # turn off the preview so the monitor can go black when the pi sleeps 
         viewing=False
         GPIO.output(17, GPIO.LOW) #turn off light1
         lighting1=False
         GPIO.output(18, GPIO.LOW) #turn off light2
         s.write(('m5 \n').encode('utf-8')) #turn off the spindle power (light 2)
         lighting2=False
         if disable_hard_limits: 
           s.write(('$21=1 \n').encode('utf-8')) # turn hard limits back on
           print('hard limits enabled')
         stopit=False
         
def goto_b(event):
         global xcol,yrow,mx,my,mz,corner,samp,pose_txt,samps
         samps=int(sampse.get()) 
         corner='unset'
         canvas.update()
         pose_txt=str(pose.get())
         pose_txt=pose_txt.replace(" ", "") #get rid of spaces
         pose_txt=pose_txt.rstrip("\r\n") # get rid of carrage return
         samp=0
         pose_txtt=pose_txt
         #first deal with the sub-sample character if present
         if not pose_txt[-1].isdigit(): # sub-sample is specified
             if pose_txt[-1] in Ualphabet[0:samps]:samp=Ualphabet.find(pose_txt[-1])
             if pose_txt[-1] in Lalphabet[0:samps]:samp=Lalphabet.find(pose_txt[-1])
             pose_txtt=pose_txt[0:-1]
         if pose_txtt[0].isdigit(): # now see if it is in number format
             numb=int(pose_txtt) 
             numb-=1
             if numb<nx*ny and numb>=0:
                 yrow=int(numb/nx)
                 xcol=numb-(yrow*nx)
                 print('yrow,xcol',yrow, xcol)
                 mcoords()
             else:
                 canvas.create_rectangle(2,2,318,60,fill='white')
                 canvas.create_text(160,27,text=("input error"),font="Helvetia 10")
                 canvas.update()
         else: # assume it is letter then number format
           let0=pose_txtt[0]
           num0=int(pose_txtt[1:])
           if ((let0 in alphabet) and (num0 <= nx)): 
             yrow=alphabet.index(let0) 
             if yrow>(ny-1): 
               yrow=yrow-ny
             xcol=num0-1
             mcoords()
           else:
             canvas.create_rectangle(2,2,318,60,fill='white')
             canvas.create_text(160,27,text=("input error"),font="Helvetia 10")
             canvas.update()

def prev_bl(event):
         global xcol,yrow,samp,mx,my,mz,corner,samps
         samps=int(sampse.get()) 
         corner='unset'
         canvas.create_rectangle(2,2,318,60,fill='white')
         if samp>0:
             samp-=1
             mcoords()
         elif xcol>0:
             xcol-=1
             samp=samps-1
             mcoords()
         elif yrow>0:
             yrow-=1
             xcol=nx-1
             samp=samps-1
             mcoords()
         else:
             canvas.create_text(160,27,text=("cannot reverse beyond the first sample"),font="Helvetia 10")
             canvas.update()

def prev_br(event):
        global xcol,yrow,mx,my,mz,corner,samps
        samps=int(sampse.get()) 
        canvas.create_rectangle(2,2,318,60,fill='white')
        yrow-=1
        if yrow == -1: yrow=ny-1
        mcoords()

def next_bl(event):
         global xcol,yrow,samp,mx,my,mz,corner,samps
         samps=int(sampse.get()) 
         corner='unset'
         canvas.create_rectangle(2,2,318,60,fill='white')
         if samp<(samps-1):
             samp+=1
             mcoords()
         elif xcol<(nx-1):
             xcol+=1
             samp=0
             mcoords()
         elif yrow<(ny-1):
             yrow+=1
             xcol=0
             samp=0
             mcoords()
         else:
             canvas.create_text(160,27,text=("cannot advance beyond the last sample"),font="Helvetia 10")
             canvas.update()

def next_br(event):
         global xcol,yrow,mx,my,mz,corner,samps
         samps=int(sampse.get()) 
         corner='unset'
         canvas.create_rectangle(2,2,318,60,fill='white')
         yrow+=1
         if yrow == 8: yrow=0
         mcoords()

root = tk.Tk()
root.title('AMiGUI v1.0')
root.geometry('320x637+1597+30')

root.bind('<Button-1>', left_click) #left click
#root.bind('<Button-3>', right_click) #right click
root.bind('<Motion>', motion)

canvas = tk.Canvas(root, width=320, height=637)
canvas.pack()
canvas.create_rectangle(0,0,320,637, width=0, fill="white") #entire window
#bounding boxes
canvas.create_rectangle(5,65,40,335, width=2, outline="darkblue",fill="lightgrey") #z setting
canvas.create_rectangle(45,65,315,335, width=2, outline="darkblue",fill="lightgrey") #xy setting
canvas.create_line(45, 200, 315, 200, width=2) #horizontal for xy
canvas.create_line(180, 65, 180, 335, width=2)  #vertical for xy
canvas.create_line(5, 200, 40, 200, width=2)   #horizontal for z
canvas.create_line(15, 120, 30, 120,fill="red")   #z lines
canvas.create_line(15, 160, 30, 160,fill="red")   #z lines
canvas.create_line(15, 240, 30, 240,fill="red")   #z lines
canvas.create_line(15, 280, 30, 280,fill="red")   #z lines
canvas.create_oval(60, 80, 300, 320, outline="red") #outer circle
canvas.create_oval(100, 120, 260, 280, outline = "red") #middle circle
canvas.create_oval(140, 160, 220, 240, outline="red") #inner circle
#labels for the xy and z areas
canvas.create_text(295,190,fill="darkblue",font="Helvetia 12 bold",text="+X")
canvas.create_text(60,190,fill="darkblue",font="Helvetia 12 bold",text="-X")
canvas.create_text(197,75,fill="darkblue",font="Helvetia 12 bold",text="+Y")
canvas.create_text(197,325,fill="darkblue",font="Helvetia 12 bold",text="-Y")
canvas.create_text(20,80,fill="darkblue",font="Helvetia 12 bold",text="+Z")
canvas.create_text(20,320,fill="darkblue",font="Helvetia 12 bold",text="-Z")

# corner alignment tool
canvas.create_rectangle(5,340,138,443,width=3,fill="lightgrey")

tlButton = tk.Button(root, text = "TL",font="Helvetia 12")
tlButton.configure(width = 3, background = "skyblue1",  activebackground = "green", relief = tk.RAISED)
tlButton_window = canvas.create_window(10,345, anchor = tk.NW, window=tlButton)
tlButton.bind('<Button-1>',tl_left_b)
tlButton.bind('<Button-3>',tl_right_b)

trButton = tk.Button(root, text = "TR",font="Helvetia 12")
trButton.configure(width = 3, background = "skyblue1",  activebackground = "green", relief = tk.RAISED)
trButton_window = canvas.create_window(75,345, anchor = tk.NW, window=trButton)
trButton.bind('<Button-1>',tr_b)

blButton = tk.Button(root, text = "BL",font="Helvetia 12")
blButton.configure(width = 3, background = "skyblue1",  activebackground = "green", relief = tk.RAISED)
blButton_window = canvas.create_window(10,405, anchor = tk.NW, window=blButton)
blButton.bind('<Button-1>',bl_b)

brButton = tk.Button(root, text = "BR",font="Helvetia 12")
brButton.configure(width = 3, background = "skyblue1",  activebackground = "green", relief = tk.RAISED)
brButton_window = canvas.create_window(75,405, anchor = tk.NW, window=brButton)
brButton.bind('<Button-1>',br_b)

setButton = tk.Button(root, text = "SET",font="Helvetia 12 bold")
setButton.configure(width = 3, background = "yellow",  activebackground = "green", relief = tk.RAISED)
setButton_window = canvas.create_window(40,376, anchor = tk.NW, window=setButton)
setButton.bind('<Button-1>',set_b)

# view, reset, quit, snap, run
viewButton = tk.Button(root, text = "VIEW",font="Helvetia 12 bold",fg="black")
viewButton.configure(width = 10, background="orange", activebackground = "green", relief = tk.RAISED)
viewButton_window = canvas.create_window(160,342, anchor = tk.NW, window=viewButton)
viewButton.bind('<Button-1>',view_b)

resetButton = tk.Button(root, text = "reset origin",font="Helvetia 10")
resetButton.configure(width = 7, background = "lightgrey",  activebackground = "green", relief = tk.RAISED)
resetButton_window = canvas.create_window(145,380, anchor = tk.NW, window=resetButton)
resetButton.bind('<Button-1>',reset_b)
resetButton.bind('<Button-3>',reset_br)

closeButton = tk.Button(root, text = "stop/close",font="Helvetia 10")
closeButton.configure(width = 7, background = "lightgrey",  activebackground = "green", relief = tk.RAISED)
closeButton_window = canvas.create_window(233,380, anchor = tk.NW, window=closeButton)
closeButton.bind('<Button-1>',close_b)

light1Button = tk.Button(root, text = "light1",font="Helvetia 10")
light1Button.configure(width = 7, background = "lightgrey",  activebackground = "green", relief = tk.RAISED)
light1Button_window = canvas.create_window(145,415, anchor = tk.NW, window=light1Button)
light1Button.bind('<Button-1>',light1_b)

light2Button = tk.Button(root, text = "light2",font="Helvetia 10")
light2Button.configure(width = 7, background = "lightgrey",  activebackground = "green", relief = tk.RAISED)
light2Button_window = canvas.create_window(233,415, anchor = tk.NW, window=light2Button)
light2Button.bind('<Button-1>',light2_b)

snapButton = tk.Button(root, text = "SNAP IMAGE",font="Helvetia 12 bold",fg="white")
snapButton.configure(width = 10, background = "medium blue",  activebackground = "green", relief = tk.RAISED)
snapButton_window = canvas.create_window(175,452, anchor = tk.NW, window=snapButton)
snapButton.bind('<Button-1>',snap_b)
snapButton.bind('<Button-3>',snap_br)

runButton = tk.Button(root, text = "RUN",font="Helvetia 12 bold",fg="yellow")
runButton.configure(width = 10, background = "black",  activebackground = "green", relief = tk.RAISED)
runButton_window = canvas.create_window(175,491, anchor = tk.NW, window=runButton)
runButton.bind('<Button-1>',run_b)

# manual movement
canvas.create_rectangle(5,450,168,525,width=3,fill="lightgrey")  

gotoButton = tk.Button(root, text = "go to")
gotoButton.configure(width = 5, background = "cyan2",  activebackground = "green", relief = tk.RAISED)
gotoButton_window = canvas.create_window(30,458, anchor = tk.NW, window=gotoButton)
gotoButton.bind('<Button-1>',goto_b)

pose = tk.Entry(canvas)
pose.insert(10,'A1')
canvas.create_window(127,472, width=50, window = pose) # manual position entry box

prevButton = tk.Button(root, text = "prev")
prevButton.configure(width = 5, background = "cyan2",  activebackground = "green", relief = tk.RAISED)
prevButton_window = canvas.create_window(15,490, anchor = tk.NW, window=prevButton)
prevButton.bind('<Button-1>',prev_bl)
prevButton.bind('<Button-3>',prev_br)

nextButton = tk.Button(root, text = "next")
nextButton.configure(width = 5, background = "cyan2",  activebackground = "green", relief = tk.RAISED)
nextButton_window = canvas.create_window(86,490, anchor = tk.NW, window=nextButton)
nextButton.bind('<Button-1>',next_bl)
nextButton.bind('<Button-3>',next_br)

# automated imaging parameters
canvas.create_rectangle(5,532,315,634,width=3,fill="lightgrey")  

updateButton = tk.Button(root, text = "write/update",font="helvetica 10") # update file
updateButton.configure(width = 8, background = "yellow",  activebackground = "green", relief = tk.RAISED)
updateButton_window = canvas.create_window(10,541, anchor = tk.NW, window=updateButton)
updateButton.bind('<Button-1>',update_b)

readButton = tk.Button(root, text = "read file",font="helvetica 10") # read file
readButton.configure(width = 8, background = "yellow",  activebackground = "green", relief = tk.RAISED)
readButton_window = canvas.create_window(10,573, anchor = tk.NW, window=readButton)
readButton.bind('<Button-1>',read_b)

filee = tk.Entry(canvas)
filee.insert(0,fname)
canvas.create_window(154,549, width=110, window = filee) # manual position entry box

canvas.create_text(227,548,text="nx:",font="Helvetia 10",fill="black") #nx
nxe = tk.Entry(canvas)
nxe.insert(0,nx)
canvas.create_window(253,549, width=26, window = nxe) 

canvas.create_text(280,548,text="ny:",font="Helvetia 10",fill="black") #ny
nye = tk.Entry(canvas)
nye.insert(0,ny)
canvas.create_window(298,549, width=14, window = nye) 

canvas.create_text(133,572,text="n_images:",font="Helvetia 10",fill="black") #n_images
nimge = tk.Entry(canvas)
nimge.insert(0,nimages)
canvas.create_window(179,574, width=21, window = nimge) 

canvas.create_text(231,572,text="Z-spacing:",font="Helvetia 10",fill="black") # z spacing
zspe = tk.Entry(canvas)
zspe.insert(0,zstep)
canvas.create_window(288,574, width=40, window = zspe) 

canvas.create_text(133,596,text="sample ID:",font="Helvetia 10",fill="black") # sample ID: 
sIDe = tk.Entry(canvas)
sIDe.insert(0,sID)
canvas.create_window(235,596, width=132, window = sIDe)

canvas.create_text(38,618,text="plate ID:",font="Helvetia 10",fill="black") # plate ID: 
IDe = tk.Entry(canvas)
IDe.insert(0,nroot)
canvas.create_window(138,618, width=132, window = IDe)

canvas.create_text(250,618,text="samples/pos:",font="Helvetia 10",fill="black") # sub-samples
sampse = tk.Entry(canvas)
sampse.insert(0,samps)
canvas.create_window(302,618, width=14, window = sampse) 

#start message
canvas.create_text(160,32,text=(" The corner samples must be centered and \n in focus before imaging. Use blue buttons \n to check alignment, and XYZ windows to \n make corrections.  Good luck!!"),font="Helvetia 10",fill="darkblue")

canvas.update()
fname=str(filee.get())
root.update()

root.mainloop()

print('\n Hope you find what you\'re looking for!  \n')
GPIO.output(17, GPIO.LOW) #turn off light1
GPIO.output(18, GPIO.LOW) #turn off light2
s.write(('m5 \n').encode('utf-8')) #turn off light2
s.close() # Close serial port 
camera.stop_preview() # stop preview
