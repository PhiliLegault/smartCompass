#!/usr/bin/python
import time
import serial 
import geopy.distance
from math import sin, cos, sqrt, atan2, radians, degrees
import math
from sense_hat import SenseHat
from threading import Thread
import threading
# Imports for rfm9x functionality
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
import adafruit_rfm9x
import sys



#### Map Coordinates
dorvalLat = 45.432023
dorvalLon = -73.740622

mtRoyalLat = 45.503689 
mtRoyalLon = -73.602551

carfourLat = 45.570101
carfourLon = -73.752392

bizardLat = 45.487648
bizardLon = -73.887209

ericssonDestLat = 45.491565
ericssonDestLon = -73.727393



# SenseHat setup
sense = SenseHat()
sense.set_rotation(0)
sense.clear()
sense.get_compass()

#gps setup
gps = serial.Serial("/dev/ttyUSB0", baudrate = 9600)



#global variables for sensor data
destinationYaw = 0 
friendYaw = 0
directionBearingDest = 0
distanceToTravelDest = 0
directionBearingFriend = 0
distanceToTravelFriend = 0
compassYaw = 0
compassRoll = 0
compassPitch = 0
lastMsg = ""
compassOffset = 0
offset = 0
currentCoordinate = (0, 0)
destinationCoordinate = (0, 0)
friendCoordinate = (0, 0)


#sensehat led defintions  
B = (0, 0, 255)
R = (255, 0, 0)
friendPoint = (255, 255, 255)
led_loop = [4, 5, 6, 7, 15, 23, 31, 39, 47, 55, 63, 62, 61, 60, 59, 58, 57, 56, 48, 40, 32, 24, 16, 8, 0, 1, 2, 3]
prev_x = 0
prev_y = 0
led_degree_ratio = len(led_loop) / 360.0




def dataLogger():
        while True:
                time.sleep(3)
                print("current Coordinate: %s" % (currentCoordinate,))
                print("destination Coordinate %s" % (destinationCoordinate,))
                print("friend Coordinate %s" % (friendCoordinate,))
                print("compass value %d" % (compassYaw))
                print("direction bearing destination: %d" % (directionBearingDest))
                print("direction bearing friend: %d" % (directionBearingFriend))
                print("distance to travel destination: %d" % (distanceToTravelDest))
                print("distance to travel friend: %d" % (distanceToTravelFriend))
                print("final destination yaw value: %d" % (destinationYaw))
                print("final friend yaw value: %d" % (friendYaw))
                print("last message: %s" % (lastMsg,))
                print("\n\n") 



#function to get distance to destination coordinates 
def getDistance(destCoor):
        distanceToTravel = geopy.distance.vincenty((currentCoordinate[0], currentCoordinate[1]), destCoor).m
        return distanceToTravel



def calculate_compass_bearing(destCoor):
        lat1 = math.radians(currentCoordinate[0])
        lat2 = math.radians(destCoor[0])
        diffLong = math.radians(destCoor[1] - currentCoordinate[1])
        x = math.sin(diffLong) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
                * math.cos(lat2) * math.cos(diffLong))
        initial_bearing = math.atan2(x, y)
        initial_bearing = math.degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360
        return compass_bearing


#collect pitch, yaw and roll values from magnetometer 
def compassSensorData():
        while True:
                sense.set_imu_config(False, True, True) # compass disabled
                orientation = sense.get_orientation()
                global compassYaw
                compassYaw = round(float("{yaw}".format(**orientation)),1)
                # compensate for faulty sensehat implementation 
                compassYaw = (compassYaw + compassOffset) % 360
                global compassRoll
                compassRoll = round(float("{roll}".format(**orientation)),1)
                global compassPitch
                compassPitch = round(float("{pitch}".format(**orientation)),1)


#function to convert lat and long coordinates to decimal formatting 
def getDecimalCoordinate(coordinate):
        #convert coordinate from string to float
        coordinate = float(coordinate)
        #get hour value of coordinate
        preDecimal = str(coordinate)[:2]
        #get minute and second value and divide by 60
        postDecimal = str(coordinate)[2:]
        postDecimalValue = float(postDecimal)/60
        decimalCoordinateValue = float(preDecimal) + postDecimalValue 
        return decimalCoordinateValue


#start gps sensor
#gather long and lat coordinates
#convert to decimal value
def gpsSensorData():
        while True:
                time.sleep(1)

                line = gps.readline()
                try: 
                        line = str(line, "utf-8")
                except:
                        print("Something blew up. Retrying gps fix later. ")
                else:
                        data = line.split(",")
                        if data[0] == "$GPRMC":
                                if data[2] == "A":
                                        decimalLat = getDecimalCoordinate(data[3])
                                        #change to negative because value is west
                                        decimalLon = (getDecimalCoordinate(data[5])) * -1
                                        global currentCoordinate
                                        currentCoordinate = (decimalLat, decimalLon)
                                else:
                                        print("no gps fix :(")
                                
                                


# used to redefine arrow colors based on distance
def redefine_arrow_color():        
        global arrow_thin_north
        arrow_thin_north = [
        B, B, B, W, W, B, B, B,
        B, B, W, W, W, W, B, B,
        B, W, W, W, W, W, W, B,
        W, W, B, W, W, B, W, W,
        B, B, B, W, W, B, B, B,
        B, B, B, W, W, B, B, B,
        B, B, B, W, W, B, B, B,
        B, B, B, W, W, B, B, B                
        ]

        global arrow_thin_east
        arrow_thin_east = [
        B, B, B, B, W, B, B, B,
        B, B, B, B, W, W, B, B,
        B, B, B, B, B, W, W, B,
        W, W, W, W, W, W, W, W,
        W, W, W, W, W, W, W, W,
        B, B, B, B, B, W, W, B,
        B, B, B, B, W, W, B, B,
        B, B, B, B, W, B, B, B                
        ]

        global arrow_thin_south
        arrow_thin_south = [
        B, B, B, W, W, B, B, B,
        B, B, B, W, W, B, B, B,
        B, B, B, W, W, B, B, B,
        B, B, B, W, W, B, B, B,
        W, W, B, W, W, B, W, W,
        B, W, W, W, W, W, W, B,
        B, B, W, W, W, W, B, B,
        B, B, B, W, W, B, B, B                
        ]


        global arrow_thin_west
        arrow_thin_west = [
        B, B, B, W, B, B, B, B,
        B, B, W, W, B, B, B, B,
        B, W, W, B, B, B, B, B,
        W, W, W, W, W, W, W, W,
        W, W, W, W, W, W, W, W,
        B, W, W, B, B, B, B, B,
        B, B, W, W, B, B, B, B,
        B, B, B, W, B, B, B, B                
        ]

        global arrow_thin_corner_NE
        arrow_thin_corner_NE = [
        B, B, B, W, W, W, W, W,
        B, B, B, B, B, W, W, W,
        B, B, B, B, W, W, W, W,
        B, B, B, W, W, W, B, W,
        B, B, W, W, W, B, B, W,
        B, W, W, W, B, B, B, B,
        W, W, W, B, B, B, B, B,
        W, W, B, B, B, B, B, B
        ]

        global arrow_thin_corner_SE
        arrow_thin_corner_SE = [
        W, W, B, B, B, B, B, B,
        W, W, W, B, B, B, B, B,
        B, W, W, W, B, B, B, B,
        B, B, W, W, W, B, B, W,
        B, B, B, W, W, W, B, W,
        B, B, B, B, W, W, W, W,
        B, B, B, B, B, W, W, W,
        B, B, B, W, W, W, W, W
        ]

        global arrow_thin_corner_SW
        arrow_thin_corner_SW = [
        B, B, B, B, B, B, W, W,
        B, B, B, B, B, W, W, W,
        B, B, B, B, W, W, W, B,
        W, B, B, W, W, W, B, B,
        W, B, W, W, W, B, B, B,
        W, W, W, W, B, B, B, B,
        W, W, W, B, B, B, B, B,
        W, W, W, W, W, B, B, B
        ]

        global arrow_thin_corner_NW
        arrow_thin_corner_NW = [
        W, W, W, W, W, B, B, B,
        W, W, W, B, B, B, B, B,
        W, W, W, W, B, B, B, B,
        W, B, W, W, W, B, B, B,
        W, B, B, W, W, W, B, B,
        B, B, B, B, W, W, W, B,
        B, B, B, B, B, W, W, W,
        B, B, B, B, B, B, W, W
        ]

        global arrow_bold
        arrow_bold = [
        R, R, R, W, W, R, R, R,
        R, R, W, W, W, W, R, R,
        R, W, W, W, W, W, W, R,
        W, W, W, W, W, W, W, W,
        R, R, W, W, W, W, R, R,
        R, R, W, W, W, W, R, R,
        R, R, W, W, W, W, R, R,
        R, R, W, W, W, W, R, R
        ]
        global arrow_bold_quasi
        arrow_bold_quasi = [
        W, W, W, W, W, W, W, W,
        R, W, W, W, W, W, W, W,
        R, R, W, W, W, W, W, W,
        R, W, W, W, W, W, W, W,
        W, W, W, W, W, W, W, W,
        W, W, W, W, W, W, W, W,
        W, W, W, W, W, R, W, W,
        R, W, W, W, R, R, R, W
        ]

def drawDestinationArrow():
        global W
        if distanceToTravelDest < 5000:
                W = (0, 255, 0)
        elif distanceToTravelDest < 10000:
                W = (255, 255, 0)
        else:
                W = (255, 0, 0)


        redefine_arrow_color()
        global destinationYaw
        destinationYaw=(360 - compassYaw + directionBearingDest)%360

        drawFriendArrow()



        if (compassRoll <= 45 or compassRoll >= 315) and (compassPitch <= 45 or compassPitch >= 315):
                if destinationYaw <= 45:
                        arrow_thin_north[offset] = friendPoint
                        sense.set_pixels(arrow_thin_north)
                elif destinationYaw < 90:
                        arrow_thin_corner_NE[offset] = friendPoint
                        sense.set_pixels(arrow_thin_corner_NE)
                elif destinationYaw < 135:
                        arrow_thin_east[offset] = friendPoint
                        sense.set_pixels(arrow_thin_east)
                elif destinationYaw < 180:
                        arrow_thin_corner_SE[offset] = friendPoint
                        sense.set_pixels(arrow_thin_corner_SE)
                elif destinationYaw < 225:
                        arrow_thin_south[offset] = friendPoint
                        sense.set_pixels(arrow_thin_south)
                elif destinationYaw < 270:
                        arrow_thin_corner_SW[offset] = friendPoint
                        sense.set_pixels(arrow_thin_corner_SW)
                elif destinationYaw < 315:
                        arrow_thin_west[offset] = friendPoint
                        sense.set_pixels(arrow_thin_west)
                else:
                        arrow_thin_corner_NW[offset] = friendPoint
                        sense.set_pixels(arrow_thin_corner_NW)

        elif (compassRoll > 45 and compassRoll <= 180) and (compassPitch <= 45 or compassPitch >= 315):
                sense.set_pixels(arrow_bold)
                sense.set_rotation(0)
        elif (compassRoll > 45 and compassRoll <= 180) and (compassPitch > 45 and compassPitch <= 67.5):
                sense.set_pixels(arrow_bold_quasi)
                sense.set_rotation(0)
        elif (compassRoll > 45 and compassRoll <= 180) and (compassPitch > 67.5 and compassPitch <= 90):
                sense.set_pixels(arrow_bold)
                sense.set_rotation(90)
        elif (compassRoll > 45 and compassRoll <= 180) and (compassPitch < 315 and compassPitch >= 292.5):
                sense.set_pixels(arrow_bold_quasi)
                sense.set_rotation(270)
        elif (compassRoll > 45 and compassRoll <= 180) and (compassPitch < 292.5 and compassPitch >= 270):
                sense.set_pixels(arrow_bold)
                sense.set_rotation(270)
        elif (compassRoll > 180 and compassRoll < 315) and (compassPitch <= 45 or compassPitch >= 315):
                sense.set_pixels(arrow_bold)
                sense.set_rotation(180)
        elif (compassRoll > 180 and compassRoll < 315) and (compassPitch > 45 and compassPitch <= 67.5):
                sense.set_pixels(arrow_bold_quasi)
                sense.set_rotation(90)
        elif (compassRoll > 180 and compassRoll < 315) and (compassPitch > 67.5 and compassPitch <= 90):
                sense.set_pixels(arrow_bold)
                sense.set_rotation(90)
        elif (compassRoll > 180 and compassRoll < 315) and (compassPitch < 315 and compassPitch >= 292.5):
                sense.set_pixels(arrow_bold_quasi)
                sense.set_rotation(180)
        elif (compassRoll > 180 and compassRoll < 315) and (compassPitch < 292.5 and compassPitch >= 270):
                sense.set_pixels(arrow_bold)
                sense.set_rotation(270)
        elif (compassPitch <= 90) and (compassRoll <= 45 or compassRoll >= 315):
                sense.set_pixels(arrow_bold)
                sense.set_rotation(90)
        elif (compassPitch >= 270) and (compassRoll <= 45 or compassRoll >= 315):
                sense.set_pixels(arrow_bold)
                sense.set_rotation(270)
        else:
                sense.clear()
        
def drawFriendArrow():
        global friendYaw
        friendYaw = (360 - compassYaw + directionBearingFriend)%360
        global led_degree_ratio
        led_index = int(led_degree_ratio * friendYaw)
        global led_loop
        global offset
        offset = led_loop[led_index - 1]


def sendCoordinateData():
        while True:
                # Throttle to < 1 Hz for operation frequency.
                time.sleep(1)

                coorStr = str(currentCoordinate)
                test2 = bytes(coorStr,"utf-8")
                try:
                        rfm9x.send(test2)
                except RuntimeError:
                        print("LoRA disconnected plz reconnect.")
                else:
                        print("sent message!")      
                        


def receiveCoordinateData():
        while True:
                packet = None
                packet = rfm9x.receive(timeout=3)
                if packet is None:
                        print("- Waiting for PKT -")
                else:
                        prev_packet = packet
                        packet_text = str(prev_packet, "utf-8")
                        global lastMsg
                        lastMsg = packet_text
                        sentCoor = lastMsg
                        sentCoor = sentCoor.replace("(", "")
                        sentCoor = sentCoor.replace(")", "")
                        sentCoor = sentCoor.split(",")
                        sentLat = float(sentCoor[0])
                        sentLon = float(sentCoor[1])
                        global friendCoordinate
                        friendCoordinate = (sentLat, sentLon)
                        print(packet_text)
                time.sleep(1)


def calibrateCompassNorthFace():
        #Calibrate Compass by setting to north
        input("Place the compass facing north and press enter")
        orientation = sense.get_orientation()
        compassInitValue = round(float("{yaw}".format(**orientation)),1)        
        global compassOffset
        compassOffset = 360 - compassInitValue


#set up LoRa Coms
# # Configure RFM9x LoRa Radio
CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

#Attempt to set up the RFM9x Module
try:
    rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 915.0)
    print("RFM9x detected")
except RuntimeError:
    # Thrown on version mismatch
    print("RFM9x: ERROR")

rfm9x.tx_power = 23
prev_packet = None


calibrateCompassNorthFace()


currentDestinationNumber = ''
#choose destination for demo since no GPS
while True:
        print("Choose your destination")
        print("[1] Enter 1 to set your destination to Ericsson")
        print("[2] Enter 2 to set your destination to Carfour Laval") 
        print("[3] Enter 3 to set your destination to Mt Royal")
        print("[4] Enter 4 to set your destination to Dorval Island")
        print("[5] Enter 5 to set your destination to Bizard Island")
        print("[q] Enter q to quit.")
        currentDestinationNumber = input()   

        if currentDestinationNumber == '1':
                destinationCoordinate = (ericssonDestLat, ericssonDestLon) 
                break
        elif currentDestinationNumber == '2':
                destinationCoordinate = (carfourLat, carfourLon)
                break
        elif currentDestinationNumber == '3':
                destinationCoordinate = (mtRoyalLat, mtRoyalLon)
                break
        elif currentDestinationNumber == '4':
                destinationCoordinate = (dorvalLat, dorvalLon)
                break
        elif currentDestinationNumber == '5':
                destinationCoordinate = (bizardLat, bizardLon)
                break
        elif currentDestinationNumber == 'q':
                print("Thanks Bye")
                quit()
        else:
                print("\nInvalid choice please try again\n")


# Start thread which sends current position on LoRa radio 
loraSendData = Thread(target=sendCoordinateData, args=())
loraSendData.daemon = True
loraSendData.start() 
# Start thread which receives current positions of other devices 
loraReceiveData = Thread(target=receiveCoordinateData, args=())
loraReceiveData.daemon = True
loraReceiveData.start() 
# Start thread which reveives gps coordinates for device 
geoData = Thread(target=gpsSensorData, args=())
geoData.daemon = True
geoData.start() 
# Start thread which gets compass value from hall sensors
compassData = Thread(target=compassSensorData, args=())
compassData.daemon = True
compassData.start()
# Print all values for testing purpuses 
logsData = Thread(target=dataLogger, args=())
logsData.daemon = True
logsData.start() 




while True:
        #get distance in meters between coordinate points
        distanceToTravelDest = getDistance(destinationCoordinate)
        #get distance in meters between current coor and friend coor
        distanceToTravelFriend = getDistance(friendCoordinate)
        
        #get bearing in degrees between coordinate points 
        directionBearingDest = calculate_compass_bearing(destinationCoordinate)
        #get bearing in degrees between current coor and friend coor
        directionBearingFriend = calculate_compass_bearing(friendCoordinate)

        #rotate arrow to point toward destination and change arrow color 
        drawDestinationArrow()



