import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from picamera import PiCamera
from pyzbar.pyzbar import decode
from PIL import Image, ImageDraw
import pickle

rfid = SimpleMFRC522()

betalen = 0
moet_ik_breaken = False
camera = PiCamera()
gegevens = pickle.load(open("data", "rb"))
vorig = ""
img = 0
eerste_id = ""
geld = 0
while not moet_ik_breaken:
    camera.capture("barcode.jpg")
    img = Image.open("barcode.jpg")

    for d in decode(img):
        if str(d.data.decode()) == str(7622210100092):
            moet_ik_breaken = True
        else:
            if gegevens[str(d.data.decode())]:
                if str(d.data.decode()) != vorig:
                    print("gescant")
                    betalen += gegevens[str(d.data.decode())][0]
                    vorig = str(d.data.decode())

while True:
    try:
        id, text = rfid.read()
        geld = float(text)
        if geld < betalen:
            break
        rfid.write(str(float(text)-betalen))
        print("Written")
        eerste_id = id
        GPIO.cleanup()
        break
    finally:
        GPIO.cleanup()
        
while True:
    if geld < betalen:
        break
    try:
        id, text = rfid.read()
        if eerste_id != id:
            rfid.write(str(float(text)+betalen))
            print("Written")
            eerste_id = id
            GPIO.cleanup()
            break
    finally:
        GPIO.cleanup()
