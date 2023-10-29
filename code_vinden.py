from mfrc522 import SimpleMFRC522
import mysql.connector
import RPi.GPIO as GPIO
import time

class RFid:
    def __init__(self):
        self.rfid = SimpleMFRC522()
        self.databank = Mysql()

        while True:
            id, text = self.rfid.read()
            _, Code, geld, = self.databank.get_bankkaart(id).fetchall()[0]
            print(Code)
            print(geld)
            time.sleep(1)


class Mysql:
    def __init__(self):
        self.query = None
        self.cnx = mysql.connector.connect(user='kasper', password='kasper',
                                      host='janickr-XPS-15-9560.local',
                                      database='kassa')
        self.cursor = self.cnx.cursor()

    def get_bankkaart(self, kaartID):
        self.cursor.reset()
        self.query = ("""
                        select * from bankkaarten
                        where KaartID = %s
                            """)
        self.cursor.execute(self.query, (kaartID,))
        return self.cursor

    def close(self):
        self.cursor.close()
        self.cnx.close()

RFid()
