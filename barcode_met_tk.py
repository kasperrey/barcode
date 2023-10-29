import threading
from tkinter import Button, Tk
from tkinter.ttk import *
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from picamera import PiCamera
from pyzbar.pyzbar import decode
from time import sleep
import datetime
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
    def __init__(self, betalen, databank, geluidje):
        self.rfid = SimpleMFRC522()
        moet_betalen = True
        while True:
            id, text = self.rfid.read()
            geluidje()
            _, Code, geld, = databank.get_bankkaart(id).fetchall()[0]
            if geld < betalen:
                break
            if self.code() == Code:
                print("Written")
                eerste_id = id
                geluidje()
            else:
                moet_betalen = False
            break

        while True:
            if geld < betalen:
                break
            id, text = self.rfid.read()
            if eerste_id != id:
                geluidje()
                _, Code2, geld2, = databank.get_bankkaart(id).fetchall()[0]
                if self.code() == Code2:
                    print("Written")
                    geluidje()
                break
        if moet_betalen:
            databank.update(eerste_id, geld - betalen)
            databank.update(id, geld + betalen)

    def readLine(self, line, characters):
        GPIO.output(line, GPIO.HIGH)
        if GPIO.input(12) == 1:
            GPIO.output(line, GPIO.LOW)
            return characters[0]
        if GPIO.input(16) == 1:
            GPIO.output(line, GPIO.LOW)
            return characters[1]
        if GPIO.input(20) == 1:
            GPIO.output(line, GPIO.LOW)
            return characters[2]
        if GPIO.input(21) == 1:
            GPIO.output(line, GPIO.LOW)
            return characters[3]
        GPIO.output(line, GPIO.LOW)
        return ""

    def code(self):
        ingegeven = ""
        volgende_cijfer = True
        while True:
            gedrukt = self.readLine(5, ["1", "2", "3", "A"])
            if gedrukt == "A":
                volgende_cijfer = True
            elif volgende_cijfer and gedrukt != "":
                volgende_cijfer = False
                ingegeven += gedrukt
            gedrukt = self.readLine(6, ["4", "5", "6", "B"])
            if volgende_cijfer and gedrukt != "":
                volgende_cijfer = False
                ingegeven += gedrukt
            gedrukt = self.readLine(13, ["7", "8", "9", "C"])
            if volgende_cijfer and gedrukt != "":
                volgende_cijfer = False
                ingegeven += gedrukt
            gedrukt = self.readLine(19, ["*", "0", "#", "D"])
            if gedrukt == "*":
                return ingegeven
            elif gedrukt == "#":
                ingegeven = ""
                gedrukt = ""
            if volgende_cijfer and gedrukt != "":
                volgende_cijfer = False
                ingegeven += gedrukt
            sleep(0.05)


class Product:
    def __init__(self, naam, prijs, code):
        self.naam = naam
        self.prijs = prijs
        self.code = code


class Mysql:
    def __init__(self):
        self.query = None
        self.cnx = mysql.connector.connect(user='kasper', password='kasper',
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
                        select * from bankkaarten
                        where KaartID = %s
                            """)
        self.cursor.execute(self.query, (kaartID,))
        return self.cursor

    def update(self, id, geld):
        self.cursor.reset()
        self.query = ("""
                UPDATE bankkaarten
                SET Geld = %s
                WHERE KaartID = %s;
        """)
        self.cursor.execute(self.query, (geld, id))

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
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(4, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(5, GPIO.OUT)
        GPIO.setup(6, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)
        GPIO.setup(19, GPIO.OUT)

        GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.mainloop()

    def geluidje(self):
        GPIO.output(4, GPIO.HIGH)
        sleep(0.05)
        GPIO.output(4, GPIO.LOW)
        sleep(0.05)
        GPIO.output(4, GPIO.HIGH)
        sleep(0.05)
        GPIO.output(4, GPIO.LOW)
        sleep(0.05)
        GPIO.output(4, GPIO.HIGH)
        sleep(0.05)
        GPIO.output(4, GPIO.LOW)

    def stop_scannen(self):
        self.scanner.stop = True
        RFid(self.betalen, self.mysql, self.geluidje)
        id = self.mysql.nieuw_ticket()
        for p in self.lijst_producten:
            id_product, _, _, _ = self.mysql.get_product(p.code).fetchall()[0]
            self.mysql.nieuwe_aankoop(id, id_product)
        self.mysql.cnx.commit()
        self.stop = True
        self.restart()

    def restart(self):
        for x in self.labels:
            x.destroy()
        self.labels = []
        self.stop = False
        self.button.destroy()
        self.button = Button(self.tk, text="Nieuwe klant", command=self.nieuwe_klant)
        self.button.grid(row=20)
        self.lijst_producten = []
        l = Label(self.tk, text="totaal: €0")
        l.grid(row=0)
        self.labels.append(l)
        self.betalen = 0
        self.mainloop()


    def nieuwe_klant(self):
        self.button.destroy()
        threading.Thread(target=self.scanner.loop).start()
        self.button = Button(self.tk, text="Betalen met bancontact", command=self.stop_scannen)
        self.button.grid(row=20)

    def mainloop(self):
        vorig = None
        while not self.stop:
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
                            self.geluidje()
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
                        self.geluidje()
            self.tk.update()
            self.tk.update_idletasks()
            sleep(0.02)

Systeem()
