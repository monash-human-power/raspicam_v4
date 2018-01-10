
import socket
import subprocess
from time import sleep

UDP_IP = subprocess.check_output(['hostname', '-I'])
UDP_PORT = 5005

data = "START"

sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
sock.bind((UDP_IP, UDP_PORT))

print ""
try:
    while True:
        print "Ready for button press!\n"
        data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes

        if data == "START":
            print "Received Start Command!"
            start = 0
            p1 = subprocess.Popen(["python", "datav2a.py"])
            sleep(1)
            print("Recording!\n")
        else:
            print "Received Stop Command!\n"
            start = 1
            subprocess.Popen.kill(p1)
            print("Execution Terminated.")
            p3 = subprocess.call(
                '/home/pi/Documents/MHP_raspicam/Accelerometers/LSM9DS1/BumpTest_Code/Shell_Scripts/sendcsv.sh')
            sleep(1)
except KeyboardInterrupt:
    if data == "START":
        subprocess.Popen.kill(p1)
        print("\n\nExecution Terminated.")
        p3 = subprocess.call('/home/pi/Documents/MHP_raspicam/Accelerometers/LSM9DS1/BumpTest_Code/Shell_Scripts/sendcsv.sh')
        print("Program Ended.\n")
    else:
        print("\n\nProgram Ended.\n")