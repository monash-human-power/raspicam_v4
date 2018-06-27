

# ---------------------------------------------------------------------
# Last Modified:
#   8-1-2018
# Description:
#   This program is the camera master. It responds to a pushbutton input
#   to start and stop camera recording.
# ---------------------------------------------------------------------

import subprocess
import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

convert = True # Control whether or not you convert the .h264 file to a .mkv file
rec_num = 0 # Changes the starting recording number in the Videos sub-folder
velocity = 1 # change this variable to change wether Camera.py or CameraVel.py is run
recording = 1 # global flag that tells the script the pi's current recording status

GPIO.setup(22,GPIO.OUT) #Green LED
GPIO.setup(23,GPIO.OUT) #Red LED
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    print("")
    GPIO.output(22,GPIO.LOW)
    GPIO.output(23,GPIO.HIGH)
    while True:
        print("Ready!\n")

        while True:
            button_state = GPIO.input(25)
            if button_state == False:
                print("Starting Camera Recording...\n")
                recording = 1
                GPIO.output(22,GPIO.HIGH)
                GPIO.output(23,GPIO.LOW)
                break
            sleep(0.2)

	if velocity == 1:
            p1 = subprocess.Popen(["python", "/home/pi/Documents/MHP_Raspicam/CameraVel.py"])
        else:
	    p1 = subprocess.Popen(["python", "/home/pi/Documents/MHP_Raspicam/Camera.py"])
	sleep(1)

        while True:
            button_state = GPIO.input(25)
            if button_state == False:
                print("\nStopping Camera Recording...\n\n")
                subprocess.Popen.kill(p1)
                recording = 0
                if convert == True:
                    subprocess.call(
                        ["bash", "/home/pi/Documents/MHP_Raspicam/convert.sh", str(rec_num)])
                    rec_num = rec_num + 1
                    print("")
                print("Wait....\n")
                sleep(1)
                GPIO.output(22,GPIO.LOW)
                GPIO.output(23,GPIO.HIGH)
                break
            sleep(0.2)
        
except KeyboardInterrupt:
    if recording == 1:
        subprocess.Popen.kill(p1)
    print("\n\nProgram Ended.\n")
    GPIO.cleanup()