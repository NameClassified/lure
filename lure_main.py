import RPi.GPIO as gpio
import os
import cv2
import datetime
import time
from picamera import PiCamera
from picamera.array import PiRGBArray
import numpy as np
import boto3
#import serial
#import string
#import pynmea2

gpio.setmode(gpio.BCM)
gpio.setup(27, gpio.OUT)
gpio.setup(4,gpio.OUT)
gpio.setup(21, gpio.IN)
gpio.setup(26, gpio.OUT)

ACCESS_KEY = 'XXXXXXXXXXXXXXXXXXXX'
SECRET_KEY = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

client = boto3.client('s3',aws_access_key_id = ACCESS_KEY, aws_secret_access_key = SECRET_KEY,region_name='us-east-2')

show_video = True
min_motion_frames = 6
camera_warmup_time = 2.5
delta_thresh = 5
resolution = tuple([640,480])
fps = 30
min_area = 5000

camera = PiCamera()
camera.resolution = resolution
camera.framerate = fps
rawCapture = PiRGBArray(camera, size=resolution)

print("INFO: Warming Up")
time.sleep(camera_warmup_time)
avg = None
last_uploaded = datetime.datetime.now()
motionCounter = 0
gpio.output(26, gpio.LOW)
t_end = time.time()+180
#port = "/dev/ttyAMA0"
#ser = serial.Serial(port, baudrate-9600, timeout = 0.5)
#dataout = pynmea2.NMEAStreamReader()
#newdata = ser.readline()
#if newdata[0:6] == "$GPRMC":
#    newmsg = pynmea2.parse(newdata)
#    lat = newmsg.latitude
#    long = newmsg.longitude
#    gps = "Latitude=" + str(lat) + " Longitude="+str(long)
while True:
    if (gpio.input(21)==1):
        gpio.output(4, gpio.HIGH)
        for f in camera.capture_continuous(rawCapture,format="bgr",use_video_port=True):
            sensor_in = gpio.input(21)
            #print("Sensor Value: " + str(sensor_in))
            frame = f.array
            timestamp = datetime.datetime.now()
            if (time.time() >= t_end):
                rawCapture.truncate(0)
                gpio.output(4, gpio.LOW)
                print("INFO: Timeout")
                break
            motion_detected = 0
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21,21), 0)
            
            if avg is None:
                print("INFO: Starting Background Model")
                avg = gray.copy().astype("float")
                rawCapture.truncate(0)
                print("INFO: Background Completed")
                continue
            cv2.accumulateWeighted(gray, avg, 0.5)
            frameDelta=cv2.absdiff(gray, cv2.convertScaleAbs(avg))
            thresh = cv2.threshold(frameDelta, delta_thresh, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            cnts, _ = cv2.findContours(thresh.copy(),cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in cnts:
                if cv2.contourArea(c) < min_area:
                    continue
                (x,y,w,h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
                motion_detected = True
                
            ts = timestamp.strftime("%A_%d_%B_%Y_%I:%M:%S")
            if motion_detected:
                motionCounter += 1
                gpio.output(26, gpio.HIGH)
                if motionCounter >= min_motion_frames:
                    #ts = timestamp.strftime("%A_%d_%B_%Y_%I:%M:%S%p")
                    cv2.putText(frame, ts, (10, frame.shape[0]-10),cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0,0,255),1)
                    #cv2.putText(frame, gps, (20, frame.shape[0]-10),cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0,0,255),1)
                    filename = "image" + ts + ".jpg"
                    cv2.imwrite(filename, frame)
                    client.upload_file(filename, 'lure-cjpan',filename)
                    last_uploaded = timestamp
                    motionCounter = 0
            else:
                motionCounter = 0
                gpio.output(26, gpio.LOW)
            
            if show_video:
                cv2.imshow("Live Trap Feed", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
            rawCapture.truncate(0)
    else:
        gpio.output(4, gpio.LOW)
        time.sleep(0.1)
