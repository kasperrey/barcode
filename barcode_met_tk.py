from threading import Thread
from tkinter import Button, Tk, Canvas, PhotoImage
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from picamera import PiCamera
from pyzbar.pyzbar import decode
from pickle import load
from time import sleep
from datetime import datetime
import mysql.connector


class Scanner:
    def __init__(self, mysql):
        self.camera = PiCamera()
        self.stop = False
        self.mysql = mysql
        self.gescant = None

    def loop(self):
        while not self.stop:
            self.camera.capture("barcode.jpg")
            img = PhotoImage(file="barcode.jpg")

            for d in decode(img):
                if len(self.mysql.get_product(d.data.decode())):
                    id, naam, prijs, barcode = self.mysql.get_product(d.data.decode())[0]
                    self.gescant = Product(naam, prijs, barcode)


class RFid:
    def __init__(self, betalen):
        self.rfid = SimpleMFRC522()
        self.stop = False
        while True:
            try:
                id, text = rfid.read()
                geld = float(text)
                if geld < betalen:
                    break
                rfid.write(str(float(text) - betalen))
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
                    rfid.write(str(float(text) + betalen))
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
        self.cnx = mysql.connector.connect(user='kasper', password='kasper',
                                      host='janickr-XPS-15-9560.local',
                                      database='kassa')
        self.cursor = self.cnx.cursor()

    def get_all_data(self):
        self.cursor.reset()
        self.query = ("""
        select *
        from aankoop a 
        join ticket t on a.ticketid = t.id
        join producten p on a.productid = p.id;
            """)
        self.cursor.execute(self.query)
        return self.cursor

    def get_product(self, barcode):
        self.cursor.reset()
        self.query = ("""
                select * from producten
                where barcode = %s
                    """)
        self.cursor.execute(self.query, (barcode,))
        return self.cursor

    def nieuw_ticket(self):
        self.cursor.reset()
        self.query = ("""
                        INSERT INTO ticket(datum) VALUES(%s)
                            """)
        self.cursor.execute(self.query, (datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S"),))
        self.cnx.commit()
        return cursor.lastrowid

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
        self.img = PhotoImage(file="vuilbak.jpg")
        self.stop = False
        self.tk = Tk()
        self.canvas = Canvas(tk, width=1000, height=1000)
        self.button = Button(tk, text="Nieuwe klant", command=self.nieuwe_klant)
        self.button.pack()
        self.scanner = Scanner(self.mysql)
        self.lijst_producten = []
        self.lijst_Knoppenen_teksten = []
        self.mainloop()

    def stop_scannen(self):
        betalen = 0
        self.scanner.stop = True
        for p in self.lijst_producten:
            betalen += p.prijs
        RFid(betalen)
        id = self.mysql.nieuw_ticket()
        for p in self.lijst_producten:
            self.mysql.nieuwe_aankoop(id, self.mysql.get_product(p.code))

    def delete(self, obj):
        self.lijst_producten.remove(obj)
        for knop in self.lijst_Knoppenen_teksten:
            if knop[2] == obj:
                self.lijst_Knoppenen_teksten.remove(knop)

    def producten(self):
        y = 10
        for x in range(len(self.lijst_producten)):
            if len(self.lijst_Knoppenen_teksten)-1 >= x:
                self.canvas.itemconfig(self.lijst_Knoppenen_teksten[x][0],
                                       text=self.lijst_producten.naam[x]+" €"+self.lijst_producten[x].prijs)
            else:
                text = self.canvas.create_text(500, y, text=self.lijst_producten.naam[x]+
                                                            " €"+self.lijst_producten[x].prijs)
                button = Button(tk, image=self.img, command=lambda: self.delete(self.lijst_producten[x]))
                button.place(x=600, y=y)
                self.lijst_Knoppenen_teksten.append([text, button, self.lijst_producten[x]])
        y += 50

    def nieuwe_klant(self):
        self.button.destroy()
        threading.Thread(target=self.scanner.loop).start()
        self.button = Button(tk, text="Afrekenen", command=self.stop_scannen)
        self.button.pack()

    def mainloop(self):
        vorig = None
        while True:
            if not self.scanner.stop:
                if self.scanner.gescant != vorig:
                    self.lijst_producten.append(self.scanner.gescant)
                    vorig = self.scanner.gescant
                    self.producten()
            self.tk.update()
            self.tk.update_idletasks()
            sleep(0.02)
