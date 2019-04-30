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



#global variables for sensor data
destinationYaw = 0 
friendYaw = 0
directionBearingDest = 0
distanceToTravelDest = 0
directionBearingFriend = 0
distanceToTravelFriend = 0
calibratedCompassYaw = 0
compassRoll = 0
compassPitch = 0
lastMsg = ""
compassOffset = 0
offset = 0
currentCoordinate = (0, 0)
destinationCoordinate = (0, 0)
friendCoordinate = (0, 0)



def dataLogger():
        while True:
                time.sleep(30)
                print("current Coordinate: %s" % (currentCoordinate,))
                print("destination Coordinate %s" % (destinationCoordinate,))
                print("friend Coordinate %s" % (friendCoordinate,))
                print("compass value %d" % (calibratedCompassYaw))
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
        printThrottle = 0
        while True:
                # Throttle.
                time.sleep(0.25)

                sense.set_imu_config(True, True, True) # compass disabled
                orientation = sense.get_orientation()
                compassYaw = round(float("{yaw}".format(**orientation)),1)
                # compensate for faulty sensehat implementation 
                global calibratedCompassYaw
                calibratedCompassYaw = (compassYaw + compassOffset) % 360
                global compassRoll
                compassRoll = round(float("{roll}".format(**orientation)),1)
                global compassPitch
                compassPitch = round(float("{pitch}".format(**orientation)),1)
	
                # debug 	
                if(printThrottle == 0):	
                        print("compass Yaw calibrated : " + str(calibratedCompassYaw))
                printThrottle += 1
                printThrottle %= 20 

 
def redefine_arrow_color(distanceArrowColor): 
        W = distanceArrowColor 
        #color of points
        B = (0, 0, 255)
        R = (255, 0, 0)       
        
        directionalArrows = {
                "arrow_thin_north" : [
                B, B, B, W, W, B, B, B,
                B, B, W, W, W, W, B, B,
                B, W, W, W, W, W, W, B,
                W, W, B, W, W, B, W, W,
                B, B, B, W, W, B, B, B,
                B, B, B, W, W, B, B, B,
                B, B, B, W, W, B, B, B,
                B, B, B, W, W, B, B, B                
                ],
                "arrow_thin_east" : [
                B, B, B, B, W, B, B, B,
                B, B, B, B, W, W, B, B,
                B, B, B, B, B, W, W, B,
                W, W, W, W, W, W, W, W,
                W, W, W, W, W, W, W, W,
                B, B, B, B, B, W, W, B,
                B, B, B, B, W, W, B, B,
                B, B, B, B, W, B, B, B                
                ],
                "arrow_thin_south" : [
                B, B, B, W, W, B, B, B,
                B, B, B, W, W, B, B, B,
                B, B, B, W, W, B, B, B,
                B, B, B, W, W, B, B, B,
                W, W, B, W, W, B, W, W,
                B, W, W, W, W, W, W, B,
                B, B, W, W, W, W, B, B,
                B, B, B, W, W, B, B, B                
                ],
                "arrow_thin_west" : [
                B, B, B, W, B, B, B, B,
                B, B, W, W, B, B, B, B,
                B, W, W, B, B, B, B, B,
                W, W, W, W, W, W, W, W,
                W, W, W, W, W, W, W, W,
                B, W, W, B, B, B, B, B,
                B, B, W, W, B, B, B, B,
                B, B, B, W, B, B, B, B                
                ],
                "arrow_thin_corner_NE" : [
                B, B, B, W, W, W, W, W,
                B, B, B, B, B, W, W, W,
                B, B, B, B, W, W, W, W,
                B, B, B, W, W, W, B, W,
                B, B, W, W, W, B, B, W,
                B, W, W, W, B, B, B, B,
                W, W, W, B, B, B, B, B,
                W, W, B, B, B, B, B, B
                ],
                "arrow_thin_corner_SE" : [
                W, W, B, B, B, B, B, B,
                W, W, W, B, B, B, B, B,
                B, W, W, W, B, B, B, B,
                B, B, W, W, W, B, B, W,
                B, B, B, W, W, W, B, W,
                B, B, B, B, W, W, W, W,
                B, B, B, B, B, W, W, W,
                B, B, B, W, W, W, W, W
                ],
                "arrow_thin_corner_SW" : [
                B, B, B, B, B, B, W, W,
                B, B, B, B, B, W, W, W,
                B, B, B, B, W, W, W, B,
                W, B, B, W, W, W, B, B,
                W, B, W, W, W, B, B, B,
                W, W, W, W, B, B, B, B,
                W, W, W, B, B, B, B, B,
                W, W, W, W, W, B, B, B
                ],
                "arrow_thin_corner_NW" : [
                W, W, W, W, W, B, B, B,
                W, W, W, B, B, B, B, B,
                W, W, W, W, B, B, B, B,
                W, B, W, W, W, B, B, B,
                W, B, B, W, W, W, B, B,
                B, B, B, B, W, W, W, B,
                B, B, B, B, B, W, W, W,
                B, B, B, B, B, B, W, W
                ],
                "arrow_bold" : [
                R, R, R, W, W, R, R, R,
                R, R, W, W, W, W, R, R,
                R, W, W, W, W, W, W, R,
                W, W, W, W, W, W, W, W,
                R, R, W, W, W, W, R, R,
                R, R, W, W, W, W, R, R,
                R, R, W, W, W, W, R, R,
                R, R, W, W, W, W, R, R
                ],
                "arrow_bold_quasi" : [
                W, W, W, W, W, W, W, W,
                R, W, W, W, W, W, W, W,
                R, R, W, W, W, W, W, W,
                R, W, W, W, W, W, W, W,
                W, W, W, W, W, W, W, W,
                W, W, W, W, W, W, W, W,
                W, W, W, W, W, R, W, W,
                R, W, W, W, R, R, R, W
                ]
        }
        return directionalArrows



def drawDestinationArrow():
        #changing color

        #sensehat led defintions  
        #TODO bring this all to local scope
        friendPoint = (255, 255, 255)
        #array of positions of outer loop of sensehat leds starting at north

        #define arrow color based on distance
        if distanceToTravelDest < 5000:
                arrowColor = (0, 255, 0)
        elif distanceToTravelDest < 10000:
                arrowColor = (255, 255, 0)
        else:
                arrowColor = (255, 0, 0)

        #TODO pass in W as var
        directionalArrows = redefine_arrow_color(arrowColor)
        
        global destinationYaw
        #TODO compassYaw to calibratedCompassYaw or other name 
        destinationYaw=(360 - calibratedCompassYaw + directionBearingDest)%360
        #TODO dont save offset globally 
        friendPixelPosition = findFriendPointPosition()


        #TODO make this 2 functions
        if (compassRoll <= 45 or compassRoll >= 315) and (compassPitch <= 45 or compassPitch >= 315):
                if destinationYaw <= 45:
                        arrow_thin_north = directionalArrows["arrow_thin_north"]
                        arrow_thin_north[friendPixelPosition] = friendPoint
                        sense.set_pixels(arrow_thin_north)
                elif destinationYaw < 90:
                        arrow_thin_corner_NE = directionalArrows["arrow_thin_corner_NE"]
                        arrow_thin_corner_NE[friendPixelPosition] = friendPoint
                        sense.set_pixels(arrow_thin_corner_NE)
                elif destinationYaw < 135:
                        arrow_thin_east = directionalArrows["arrow_thin_east"]
                        arrow_thin_east[friendPixelPosition] = friendPoint
                        sense.set_pixels(arrow_thin_east)
                elif destinationYaw < 180:
                        arrow_thin_corner_SE = directionalArrows["arrow_thin_corner_SE"]
                        arrow_thin_corner_SE[friendPixelPosition] = friendPoint
                        sense.set_pixels(arrow_thin_corner_SE)
                elif destinationYaw < 225:
                        arrow_thin_south = directionalArrows["arrow_thin_south"]
                        arrow_thin_south[friendPixelPosition] = friendPoint
                        sense.set_pixels(arrow_thin_south)
                elif destinationYaw < 270:
                        arrow_thin_corner_SW = directionalArrows["arrow_thin_corner_SW"]
                        arrow_thin_corner_SW[friendPixelPosition] = friendPoint
                        sense.set_pixels(arrow_thin_corner_SW)
                elif destinationYaw < 315:
                        arrow_thin_west = directionalArrows["arrow_thin_west"]
                        arrow_thin_west[friendPixelPosition] = friendPoint
                        sense.set_pixels(arrow_thin_west)
                else:
                        arrow_thin_corner_NW = directionalArrows["arrow_thin_corner_NW"]
                        arrow_thin_corner_NW[friendPixelPosition] = friendPoint
                        sense.set_pixels(arrow_thin_corner_NW)

        elif (compassRoll > 45 and compassRoll <= 180) and (compassPitch <= 45 or compassPitch >= 315):
                arrow_bold = directionalArrows["arrow_bold"]
                sense.set_pixels(arrow_bold)
                sense.set_rotation(0)
        elif (compassRoll > 45 and compassRoll <= 180) and (compassPitch > 45 and compassPitch <= 67.5):
                arrow_bold_quasi = directionalArrows["arrow_bold_quasi"]
                sense.set_pixels(arrow_bold_quasi)
                sense.set_rotation(0)
        elif (compassRoll > 45 and compassRoll <= 180) and (compassPitch > 67.5 and compassPitch <= 90):
                arrow_bold = directionalArrows["arrow_bold"]
                sense.set_pixels(arrow_bold)
                sense.set_rotation(90)
        elif (compassRoll > 45 and compassRoll <= 180) and (compassPitch < 315 and compassPitch >= 292.5):
                arrow_bold_quasi = directionalArrows["arrow_bold_quasi"]
                sense.set_pixels(arrow_bold_quasi)
                sense.set_rotation(270)
        elif (compassRoll > 45 and compassRoll <= 180) and (compassPitch < 292.5 and compassPitch >= 270):
                arrow_bold = directionalArrows["arrow_bold"]
                sense.set_pixels(arrow_bold)
                sense.set_rotation(270)
        elif (compassRoll > 180 and compassRoll < 315) and (compassPitch <= 45 or compassPitch >= 315):
                arrow_bold = directionalArrows["arrow_bold"]
                sense.set_pixels(arrow_bold)
                sense.set_rotation(180)
        elif (compassRoll > 180 and compassRoll < 315) and (compassPitch > 45 and compassPitch <= 67.5):
                arrow_bold_quasi = directionalArrows["arrow_bold_quasi"]
                sense.set_pixels(arrow_bold_quasi)
                sense.set_rotation(90)
        elif (compassRoll > 180 and compassRoll < 315) and (compassPitch > 67.5 and compassPitch <= 90):
                arrow_bold = directionalArrows["arrow_bold"]
                sense.set_pixels(arrow_bold)
                sense.set_rotation(90)
        elif (compassRoll > 180 and compassRoll < 315) and (compassPitch < 315 and compassPitch >= 292.5):
                arrow_bold_quasi = directionalArrows["arrow_bold_quasi"]
                sense.set_pixels(arrow_bold_quasi)
                sense.set_rotation(180)
        elif (compassRoll > 180 and compassRoll < 315) and (compassPitch < 292.5 and compassPitch >= 270):
                arrow_bold = directionalArrows["arrow_bold"]
                sense.set_pixels(arrow_bold)
                sense.set_rotation(270)
        elif (compassPitch <= 90) and (compassRoll <= 45 or compassRoll >= 315):
                arrow_bold = directionalArrows["arrow_bold"]
                sense.set_pixels(arrow_bold)
                sense.set_rotation(90)
        elif (compassPitch >= 270) and (compassRoll <= 45 or compassRoll >= 315):
                arrow_bold = directionalArrows["arrow_bold"]
                sense.set_pixels(arrow_bold)
                sense.set_rotation(270)
        else:
                sense.clear()
        
def findFriendPointPosition():
        led_loop = [4, 5, 6, 7, 15, 23, 31, 39, 47, 55, 63, 62, 61, 60, 59, 58, 57, 56, 48, 40, 32, 24, 16, 8, 0, 1, 2, 3]
        led_degree_ratio = len(led_loop) / 360.0
        global friendYaw
        #TODO make this a func 
        friendYaw = (360 - calibratedCompassYaw + directionBearingFriend)%360
        #TODO make this local
        led_index = int(led_degree_ratio * friendYaw)
        #TODO change name offset for something else
        friendPixelPosition = led_loop[led_index - 1]
        return friendPixelPosition


def sendCoordinateData():
        while True:
                # Writing to the LoRA is slow so no throttling needed.

                coorStr = str(currentCoordinate)
                test2 = bytes(coorStr,"utf-8")
                try:
                        rfm9x.send(test2)
                except RuntimeError:
                        print("LoRA disconnected plz reconnect.")
                else:
                        print("-- LoRA sent message! = " + coorStr)    


def receiveCoordinateData():
        while True:
                # No delay here, just keep listening with a long timeout. 
                packet = None
                packet = rfm9x.receive(timeout=5)
                if packet is None:
                        print("- Waiting for PKT -")
                else:
                        prev_packet = packet
                        try: 
                                packet_text = str(prev_packet, "utf-8")
                        except UnicodeDecodeError:
                                print("Received garbage data on LoRA. Trying again later.")
                                continue

                        global lastMsg
                        lastMsg = packet_text
                        sentCoor = lastMsg
                        sentCoor = sentCoor.replace("(", "")
                        sentCoor = sentCoor.replace(")", "")
                        sentCoor = sentCoor.split(",")
                        try:
                                sentLat = float(sentCoor[0])
                                sentLon = float(sentCoor[1])
                        except ValueError:
                                print("Received garbage data on LoRA. Trying again later.")
                                continue
                        
                        global friendCoordinate
                        friendCoordinate = (sentLat, sentLon)
                        print("- PKT recevied: " + packet_text + " -")
                


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
    print("RFM9x: ERROR. LoRA is probably not connected. Exiting")
    sys.exit(1)

rfm9x.tx_power = 23
prev_packet = None


calibrateCompassNorthFace()


currentPositionNumber = ''
#choose current postion for demo since no GPS
while True:
        print("Choose your current position")
        print("[1] Enter 1 to set your current position to Ericsson")
        print("[2] Enter 2 to set your current position to Carfour Laval")
        print("[3] Enter 3 to set your current position to Mt Royal")
        print("[4] Enter 4 to set your current position to Dorval Island")
        print("[5] Enter 5 to set your current position to Bizard Island")
        print("[q] Enter q to quit.")
        
        currentPositionNumber = input()   

        if currentPositionNumber == '1':
                currentCoordinate = (ericssonDestLat, ericssonDestLon) 
                break
        elif currentPositionNumber == '2':
                currentCoordinate = (carfourLat, carfourLon)
                break
        elif currentPositionNumber == '3':
                currentCoordinate = (mtRoyalLat, mtRoyalLon)
                break
        elif currentPositionNumber == '4':
                currentCoordinate = (dorvalLat, dorvalLon)
                break
        elif currentPositionNumber == '5':
                currentCoordinate = (bizardLat, bizardLon)
                break
        elif currentPositionNumber == 'q':
                print("Thanks Bye")
                quit()
        else:
                print("\nInvalid choice please try again\n")


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



