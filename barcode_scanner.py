import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

rfid = SimpleMFRC522()

while True:
    try:
        id, text = rfid.read()
        print(id)
    finally:
        GPIO.cleanup()
