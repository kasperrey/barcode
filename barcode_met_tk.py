import threading
from tkinter import Button, Tk
from tkinter.ttk import *
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from picamera import PiCamera
from pyzbar.pyzbar import decode
from time import sleep
from datetime import datetime
import mysql.connector
from PIL import Image


class Scanner:
    def __init__(self, mysql):
        self.camera = PiCamera()
        self.stop = False
        self.mysql = mysql
        self.gescant = None

    def loop(self):
        while not self.stop:
            self.camera.capture("barcode.jpg")
            img = Image.open("barcode.jpg")

            for d in decode(img):
                cursor = self.mysql.get_product(d.data.decode()).fetchall()
                if len(cursor) > 0:
                    id, naam, prijs, barcode = cursor[0]
                    self.gescant = Product(naam, prijs, barcode)


class RFid:
    def __init__(self, betalen, mysql):
        self.rfid = SimpleMFRC522()
        while True:
            try:
                id, text = self.rfid.read()
                _, Code, geld, = mysql.get_bankkaart(id).fetchall()[0]
                if geld < betalen:
                    break
                mysql.update(id, geld - betalen)
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
                id, text = self.rfid.read()
                if eerste_id != id:
                    _, Code, geld, = mysql.get_bankkaart(id).fetchall()[0]
                    mysql.update(id, geld + betalen)
                    print("Written")
                    GPIO.cleanup()
                    break
            finally:
                GPIO.cleanup()


class Product:
    def __init__(self, naam, prijs, code):
        self.naam = naam
        self.prijs = prijs
        self.code = code


class Mysql:
    def __init__(self):
        self.query = None
        self.cnx = mysql.connector.connect(user='', password='',
                                      host='janickr-XPS-15-9560.local',
                                      database='kassa')
        self.cursor = self.cnx.cursor()

    def get_product(self, barcode):
        self.cursor.reset()
        self.query = ("""
                select * from producten
                where barcode = %s
                    """)
        self.cursor.execute(self.query, (barcode,))
        return self.cursor

    def get_bankkaart(self, kaartID):
        self.cursor.reset()
        self.query = ("""
                        select * from Bankkaarten
                        where KaartID = %s
                            """)
        self.cursor.execute(self.query, (kaartID,))
        return self.cursor

    def update(self, id, geld):
        self.cursor.reset()
        self.query = ("""
                UPDATE Bankkaarten
                SET Geld = %s
                WHERE KaartID = %S;
        """)
        self.cursor.execute(self.query, (geld, id))
        return self.cursor

    def nieuw_ticket(self):
        self.cursor.reset()
        self.query = ("""
                        INSERT INTO ticket(datum) VALUES(%s)
                            """)
        self.cursor.execute(self.query, (datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S"),))
        self.cnx.commit()
        return self.cursor.lastrowid

    def nieuwe_aankoop(self, ticketid, productid):
        self.cursor.reset()
        self.query = ("""
                        INSERT INTO aankoop(ticketid, productid) VALUES(%s, %s)
                            """)
        self.cursor.execute(self.query, (ticketid, productid))
        self.cnx.commit()

    def close(self):
        self.cursor.close()
        self.cnx.close()


class Systeem:
    def __init__(self):
        self.mysql = Mysql()
        self.stop = False
        self.tk = Tk()
        self.button = Button(self.tk, text="Nieuwe klant", command=self.nieuwe_klant)
        self.button.grid(row=20)
        self.scanner = Scanner(self.mysql)
        self.lijst_producten = []
        self.labels = []
        l = Label(self.tk, text="totaal: €0")
        l.grid(row=0)
        self.labels.append(l)
        self.betalen = 0
        self.mainloop()

    def stop_scannen(self):
        self.scanner.stop = True
        RFid(self.betalen)
        id = self.mysql.nieuw_ticket()
        for p in self.lijst_producten:
            id_product, _, _, _ = self.mysql.get_product(p.code).fetchall()[0]
            self.mysql.nieuwe_aankoop(id, id_product)

    def nieuwe_klant(self):
        self.button.destroy()
        threading.Thread(target=self.scanner.loop).start()
        self.button = Button(self.tk, text="Betalen met bancontact", command=self.stop_scannen)
        self.button.grid(row=20)

    def mainloop(self):
        vorig = None
        while True:
            if not self.scanner.stop:
                if self.scanner.gescant:
                    if vorig:
                        if self.scanner.gescant.naam != vorig.naam:
                            self.lijst_producten.append(self.scanner.gescant)
                            vorig = self.scanner.gescant
                            self.betalen += vorig.prijs
                            for label in self.labels:
                                label.grid(row=label.grid_info()["row"]+1)
                            l = Label(self.tk, text=vorig.naam+" "+str(vorig.prijs))
                            l.grid(row=0)
                            self.labels.append(l)
                            self.labels[0].config(text=f"totaal: €{self.betalen}")
                    else:
                        self.lijst_producten.append(self.scanner.gescant)
                        vorig = self.scanner.gescant
                        self.betalen += vorig.prijs
                        for label in self.labels:
                            label.grid(row=label.grid_info()["row"] + 1)
                        l = Label(self.tk, text=vorig.naam + " " + str(vorig.prijs))
                        l.grid(row=0)
                        self.labels.append(l)
                        self.labels[0].config(text=f"totaal: €{self.betalen}")
            self.tk.update()
            self.tk.update_idletasks()
            sleep(0.02)

Systeem()
