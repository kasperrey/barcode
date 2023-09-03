from time import sleep
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

rfid = SimpleMFRC522()


while True:
    try:
        rfid.write(str(50))
        print("Written")
        break
    finally:
        GPIO.cleanup()

while True:
    id, text = rfid.read()
    print(text)
    sleep(1)
