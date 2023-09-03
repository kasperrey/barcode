from picamera import PiCamera
from pyzbar.pyzbar import decode
from PIL import Image, ImageDraw

moet_ik_breaken = False
camera = PiCamera()
global img
while not moet_ik_breaken:
    camera.capture("barcode.jpg")

    img = Image.open("barcode.jpg")

    draw = ImageDraw.Draw(img)

    for d in decode(img):
        print(d.data.decode())
        print(d.type)
        draw.rectangle(((d.rect.left, d.rect.top), (d.rect.left + d.rect.width, d.rect.top + d.rect.height)),
                       outline=(0, 0, 255), width=3)
        draw.text((d.rect.left, d.rect.top + d.rect.height), d.data.decode(),
                  (255, 0, 0))
        moet_ik_breaken = True  

img.save('barcode.jpg')
