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
lastMsg = ""
compassOffset = 0
currentCoordinate = (0, 0)
destinationCoordinate = (0, 0)
friendCoordinate = (0, 0)



def dataLogger():
        while True:
                time.sleep(3)
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
        while True:
                sense.set_imu_config(False, True, True) # compass disabled
                orientation = sense.get_orientation()
                compassYaw = round(float("{yaw}".format(**orientation)),1)
                # compensate for faulty sensehat implementation 
                global calibratedCompassYaw
                calibratedCompassYaw = (compassYaw + compassOffset) % 360
                global compassRoll
                compassRoll = round(float("{roll}".format(**orientation)),1)
                global compassPitch
                compassPitch = round(float("{pitch}".format(**orientation)),1)



def drawDestinationArrow():
        #sensehat led defintions  
        green = (0, 255, 0)
        yellow = (255, 255, 0)
        red = (255, 0, 0)
        
        B = (0, 0, 255)
        blueDisplay = [
                B, B, B, B, B, B, B, B,
                B, B, B, B, B, B, B, B,
                B, B, B, B, B, B, B, B,
                B, B, B, B, B, B, B, B,
                B, B, B, B, B, B, B, B,
                B, B, B, B, B, B, B, B,
                B, B, B, B, B, B, B, B,
                B, B, B, B, B, B, B, B                
                ]
        #define point color based on distance to destination
        if distanceToTravelDest < 5000:
                destinationPoint = green
        elif distanceToTravelDest < 10000:
                destinationPoint = yellow
        else:
                destinationPoint = red

        #define point color based on distance to friend
        if distanceToTravelFriend < 50:
                friendPoint = green
        elif distanceToTravelFriend < 100:
                friendPoint = yellow
        else:
                friendPoint = red 

        
        destinationPixelPosition = findDestinationPointPosition()
        friendPixelPosition = findFriendPointPosition()

        blueDisplay[destinationPixelPosition] = destinationPoint
        blueDisplay[friendPixelPosition] = friendPoint

        sense.set_pixels(blueDisplay)



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

def findDestinationPointPosition():
        led_loop = [4, 5, 6, 7, 15, 23, 31, 39, 47, 55, 63, 62, 61, 60, 59, 58, 57, 56, 48, 40, 32, 24, 16, 8, 0, 1, 2, 3]
        led_degree_ratio = len(led_loop) / 360.0
        global destinationYaw
        destinationYaw=(360 - calibratedCompassYaw + directionBearingDest)%360
        #TODO make this local
        led_index = int(led_degree_ratio * destinationYaw)
        #TODO change name offset for something else
        destinationPixelPosition = led_loop[led_index - 1]
        return destinationPixelPosition


def sendCoordinateData():
        while True:
                coorStr = str(currentCoordinate)
                test2 = bytes(coorStr,"utf-8")
                rfm9x.send(test2)
                print("sent message!")      
                time.sleep(1)


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



