import picamera
import pigpio
import time
import os

# Make sure the command "sudo pigpiod" is running on boot through sudo nano /etc/rc.local

record = 1
pin = 4
Pi = 3.14159
d = 0.5

pi = pigpio.pi()
pi.set_mode(pin, pigpio.INPUT)
pi.set_pull_up_down(pin, pigpio.PUD_UP)

if not pi.connected:
    exit()

with picamera.PiCamera() as camera:
    camera.resolution = (800, 480)
    camera.vflip = False
    camera.framerate = 45
    camera.start_preview()
    camera.annotate_background = picamera.Color('black')
    camera.annotate_text = '{}'.format(0.0)

    if record == 1:
        j = 0
        while os.path.exists("/home/pi/Documents/MHP_raspicam/Camera/Video/Recording_%s.h264" % j):
            j += 1
        filename = "/home/pi/Documents/MHP_raspicam/Camera/Video/Recording_%s.h264" % j
        camera.start_recording(filename)

    previous = pi.read(pin)
    prev_time = time.time()

    try:
        while True:

            next = pi.read(pin)

            if next != previous and next == 0:
                next_time = time.time()
                time_delta = float(next_time - prev_time)
                speed = (1.0 / time_delta) * Pi * d * 3.6
                camera.annotate_text = '{}'.format(round(speed, 1))
                prev_time = next_time

            if (time.time() - prev_time) > 3:
                camera.annotate_text = '{}'.format(0.0)

#	    if record == 1:
#		camera.wait_recording(0.2)

            previous = next

    except KeyboardInterrupt:
        if record == 1:
            camera.stop_recording()
