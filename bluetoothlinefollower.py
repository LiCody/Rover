import bluetooth as bt
import threading
import RPi.GPIO as GPIO
from time import sleep
from adafruit_motorkit import MotorKit
import adafruit_rgb_display.st7735 as st7735
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont

from picamera import PiCamera, Color
import io

# initalize motor, GPIO mode and Camera
kit = MotorKit()
GPIO.setmode(GPIO.BCM)
camera = PiCamera()
camera.resolution = (240, 240)
camera.start_preview()
sleep(2) # need this 2 seconds to initalize camera

#Pinouts for each sensor
sensor_farRight = 21
sensor_right = 26
sensor_middle = 16
sensor_left = 6
sensor_farLeft = 17
GPIO.setup(sensor_farRight, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(sensor_right, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(sensor_middle, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(sensor_left, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(sensor_farLeft, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

# Configuration for CS and DC pins for LCD
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)

# Config for display baudrate (default max is 24mhz):
BAUDRATE = 24000000

# Setup SPI bus using hardware SPI:
spi = board.SPI()

# Create the display:
disp = st7735.ST7735R(spi, rotation=90, bgr=True,
                       cs=cs_pin, dc=dc_pin, rst=reset_pin, baudrate=BAUDRATE)

# Create blank image for drawing.
width = disp.height
height = disp.width
image = Image.new('RGB', (width, height))

# Initialize drawing and font
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()

# Initialize padding and x parameters for LCD
padding = 5
x = 40
# bluetooth class for receiving information because recv() would otherwise block
class bluetoothThread(threading.Thread):
    def __init__(self, socket):
        # initialize variables
        threading.Thread.__init__(self)
        self.socket = socket
        self.runparam = "Stop"
    def run(self):
        try:
            while True:
                data = self.socket.recv(1024)
                if not data: # check that data isnt null
                    pass
                # assign runparam one of 6 configs
                if data.decode("UTF-8") == "Start":
                    t.runparam = "Start"
                elif data.decode("UTF-8") == "Stop":
                    t.runparam = "Stop"
                elif data.decode("UTF-8") == "Forwards":
                    t.runparam = "Forwards"
                elif data.decode("UTF-8") == "Left":
                    t.runparam = "Left"
                elif data.decode("UTF-8") == "Right":
                    t.runparam = "Right"
                elif data.decode("UTF-8") == "Back":
                    t.runparam = "Back"
                print(t.runparam)
        except (OSError, SystemExit, KeyboardInterrupt):
            print("Disconnected from Receiver")
            self.socket.close()

# for sending pictures over bluetooth
class senderThread(threading.Thread):
    def __init__(self, socket):
        threading.Thread.__init__(self)
        self.socket = socket
        camera.start_preview()
    def run(self):
        try:
            while True:
                print("sent picture")
                camera.capture("/home/pi/Desktop/image.jpeg")
                img = Image.open("/home/pi/Desktop/image.jpeg")
                # converts jpeg into a array of bytes for the 
                # android app to process
                toSend = io.BytesIO()
                img.save(toSend, format = 'jpeg')
                sleep(1) 
                self.socket.send(toSend.getvalue())
                sleep(2)
        except (OSError, SystemExit, KeyboardInterrupt):
            print("Disconnected from Sender")
            camera.stop_preview()
            self.socket.close()
#setup for bluetooth socket
server_socket = bt.BluetoothSocket(bt.RFCOMM)
server_socket.bind(("", bt.PORT_ANY))
server_socket.listen(1)

try:
    # waits for connection
    print("connecting")
    client_socket, address = server_socket.accept()
    print ("Accepted connection from "), address
    # initalize both threads, Daemon is True so that we dont need
    # to manually close it
    t = bluetoothThread(client_socket)
    t.setDaemon(True)
    t.start()
    t2 = senderThread(client_socket)
    t2.setDaemon(True)
    t2.start()
    while True:
        if t.runparam == "Start":
            print("starting")
            # Loop for fully autonomous control
            while True:
                # read each sensor
                reading_farRight = GPIO.input(sensor_farRight)
                reading_right = GPIO.input(sensor_right)
                reading_middle = GPIO.input(sensor_middle)
                reading_left = GPIO.input(sensor_left)
                reading_farLeft = GPIO.input(sensor_farLeft)
                #LCD code for displaying sensor status on screen
                draw.rectangle((0, 0, width, height), fill= "#FFFFFF")
                y = padding
                title = "Line Follower " 
                draw.text((x, y), title, font=font, fill="#000000")
                y += font.getsize(title)[1]
                sens1 = "Left Left: " + str(reading_farLeft)
                draw.text((x, y), sens1, font=font, fill="#000000")
                y += font.getsize(sens1)[1]
                sens2 = "Left: " + str(reading_left)
                draw.text((x, y), sens2, font=font, fill="#000000")
                y += font.getsize(sens2)[1]
                sens3 = "Middle: " + str(reading_middle)
                draw.text((x, y), sens3, font=font, fill="#000000")
                y += font.getsize(sens3)[1]
                sens4 = "Right: " + str(reading_right)
                draw.text((x, y), sens4, font=font, fill="#000000")
                y += font.getsize(sens4)[1]
                sens5 = "Right Right: " + str(reading_farRight)
                draw.text((x, y), sens5, font=font, fill="#000000")
                y += font.getsize(sens5)[1]
                dir = "Direction: " 
                draw.text((x, y), dir, font=font, fill="#000000")
                y += font.getsize(dir)[1]
                direct = "Left" if reading_left or reading_farLeft else "Right" if reading_right or reading_farRight else "Forward" 
                draw.text((x, y), direct, font=font, fill="#000000")
                y += font.getsize(direct)[1]

                # Display image.
                disp.image(image)
                print("reading_farRight = " + str(reading_farRight))
                print("reading_right = " + str(reading_right))	#         print("reading_top_middle = " + str(reading_top_middle))
                print("reading_middle = " + str(reading_middle))	#         print("reading_middle = " + str(reading_middle))
                print("reading_left = " + str(reading_left))	#         print("reading_middle_bottom = " + str(reading_middle_bottom))
                print("reading_farLeft = " + str(reading_farLeft))	#         print("reading_bottom = " + str(reading_bottom))
                print("--------------")	#         print("--------------")
                forwardSpeed = 0.37
                
                # forward
                if (reading_middle and not reading_right and not reading_left and not reading_farRight and not reading_farLeft):
                    kit.motor1.throttle = forwardSpeed 
                    kit.motor2.throttle = forwardSpeed + 0.0112 # this is to account for weight imbalance
                #slowforward
                elif (reading_middle):
                    kit.motor1.throttle = forwardSpeed - 0.1
                    kit.motor2.throttle = forwardSpeed + 0.0112 - 0.1 # this is to account for weight imbalance
                
                # goes straight during junctions/crosses
                elif ((reading_left and reading_right) or (reading_farLeft and reading_farRight)):
                    kit.motor1.throttle = forwardSpeed 
                    kit.motor2.throttle = forwardSpeed + 0.0112
                # right turn
                elif (reading_right and not reading_farRight):
                    # turns until reading middle sensor and not reading right sensor
                    while not reading_middle:
                        kit.motor1.throttle = 0 
                        kit.motor2.throttle = forwardSpeed + 0.0112
                        sleep(0.01)
                        reading_middle = GPIO.input(sensor_middle)
                        reading_right = GPIO.input(sensor_right) 
                # left turn
                elif (reading_left and not reading_farLeft):
                    # turns until reading middle sensor and not reading left sensor
                    while not reading_middle:
                        kit.motor1.throttle = forwardSpeed 
                        kit.motor2.throttle = 0 
                        sleep(0.01)
                        reading_middle = GPIO.input(sensor_middle)
                        reading_left = GPIO.input(sensor_left) 
                # hard right turn
                elif (reading_farRight):
                    # turns until it is lined up with the middle
                    while not reading_middle:
                        kit.motor1.throttle = -0.2 
                        kit.motor2.throttle = forwardSpeed + 0.0112
                        sleep(0.01)
                        reading_middle = GPIO.input(sensor_middle)
                        reading_farRight = GPIO.input(sensor_farRight)
                # hard left turn
                elif (reading_farLeft):
                    # turns until it is lined up with the middle
                    while not reading_middle:
                        kit.motor1.throttle = forwardSpeed 
                        kit.motor2.throttle = -0.2 
                        sleep(0.01)
                        reading_middle = GPIO.input(sensor_middle)
                        reading_farLeft = GPIO.input(sensor_farLeft)
                # no readings
                else:
                    # continues forward
                    kit.motor1.throttle = forwardSpeed 
                    kit.motor2.throttle = forwardSpeed 
                    good = False
                    # if it doesnt detect anything for 1s (roughly 5cm will stop)
                    for i in range(0, 15):
                        reading_farRight = GPIO.input(sensor_farRight)
                        reading_right = GPIO.input(sensor_right)
                        reading_middle = GPIO.input(sensor_middle)
                        reading_left = GPIO.input(sensor_left)
                        reading_farLeft = GPIO.input(sensor_farLeft)
                        #will break if any sensors are read
                        if reading_farLeft or reading_farRight or reading_left or reading_middle or reading_right:
                            good = True
                            break
                        sleep(0.04)
                    # breaks out of the autonomous loop
                    if not good:
                        t.runparam = "Stop"
                        break
                sleep(0.01)
                # allows bluetooth to break out of the autonomous loop
                if t.runparam == "Stop":
                    print("stopped")
                    kit.motor1.throttle = 0
                    kit.motor2.throttle = 0
                    break
        elif t.runparam == "Stop":
            i = 0
            # Loop for Manual Control
            while True:
                i += 1
                if t.runparam == "Left":
                    kit.motor1.throttle = 0.4
                    kit.motor2.throttle = 0
                elif t.runparam == "Right":
                    kit.motor1.throttle = 0
                    kit.motor2.throttle = 0.4
                elif t.runparam == "Forwards":
                    kit.motor1.throttle = 0.4
                    kit.motor2.throttle = 0.4
                elif t.runparam == "Back":
                    kit.motor1.throttle = -0.4
                    kit.motor2.throttle = -0.4
                elif t.runparam == "Start":
                    break 
                sleep(0.05)
                # i is needed so that we can don't pass through the loop
                if t.runparam == "Stop" and i > 20:
                    kit.motor1.throttle = 0
                    kit.motor2.throttle = 0
                    break
        
        sleep(0.1) # this corresponds to large while True
except (SystemError, OSError, KeyboardInterrupt):
    GPIO.cleanup()
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0
    camera.stop_preview()
    print("Disconnected.")
    client_socket.close()
    server_socket.close()
    print("All done.")
