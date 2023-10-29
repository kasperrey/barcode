from mfrc522 import SimpleMFRC522
import mysql.connector
import RPi.GPIO as GPIO
import time

class RFid:
    def __init__(self):
        self.rfid = SimpleMFRC522()
        self.databank = Mysql()
        self.L1 = 29
        self.L2 = 31
        self.L3 = 33
        self.L4 = 35
        self.C1 = 32
        self.C2 = 36
        self.C3 = 38
        self.C4 = 40
        GPIO.setwarnings(False)

        GPIO.setup(self.L1, GPIO.OUT)
        GPIO.setup(self.L2, GPIO.OUT)
        GPIO.setup(self.L3, GPIO.OUT)
        GPIO.setup(self.L4, GPIO.OUT)

        # Make sure to configure the input pins to use the internal pull-down resistors

        GPIO.setup(self.C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        while True:
            id, text = self.rfid.read()
            _, Code, geld, = self.databank.get_bankkaart(id).fetchall()[0]
            print("typ je code")
            c = self.code()
            print(c)
            if c == Code:
                print("kies nieuwe code")
                time.sleep(0.5)
                nieuwe_code = self.code()
                print(nieuwe_code)
                print("bevestig je nieuwe code")
                time.sleep(0.5)
                c = self.code()
                if c == nieuwe_code:
                    self.databank.update(id, nieuwe_code)
                    print("nieuwe code")
                    print(nieuwe_code)
            break
        self.databank.cnx.commit()
        self.databank.close()

    def readLine(self, line, characters):
        GPIO.output(line, GPIO.HIGH)
        if GPIO.input(self.C1) == 1:
            GPIO.output(line, GPIO.LOW)
            return characters[0]
        if GPIO.input(self.C2) == 1:
            GPIO.output(line, GPIO.LOW)
            return characters[1]
        if GPIO.input(self.C3) == 1:
            GPIO.output(line, GPIO.LOW)
            return characters[2]
        if GPIO.input(self.C4) == 1:
            GPIO.output(line, GPIO.LOW)
            return characters[3]
        GPIO.output(line, GPIO.LOW)
        return ""

    def code(self):
        ingegeven = ""
        volgende_cijfer = True
        while True:
            gedrukt = self.readLine(self.L1, ["1", "2", "3", "A"])
            if gedrukt == "A":
                volgende_cijfer = True
            elif volgende_cijfer and gedrukt != "":
                volgende_cijfer = False
                ingegeven += gedrukt
                print(ingegeven)
            gedrukt = self.readLine(self.L2, ["4", "5", "6", "B"])
            if volgende_cijfer and gedrukt != "":
                volgende_cijfer = False
                ingegeven += gedrukt
                print(ingegeven)
            gedrukt = self.readLine(self.L3, ["7", "8", "9", "C"])
            if volgende_cijfer and gedrukt != "":
                volgende_cijfer = False
                ingegeven += gedrukt
                print(ingegeven)
            gedrukt = self.readLine(self.L4, ["*", "0", "#", "D"])
            if gedrukt == "*":
                return ingegeven
            elif gedrukt == "#":
                ingegeven = ""
                gedrukt = ""
            if volgende_cijfer and gedrukt != "":
                volgende_cijfer = False
                ingegeven += gedrukt
                print(ingegeven)
            time.sleep(0.01)


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

    def update(self, id, code):
        self.cursor.reset()
        self.query = ("""
                UPDATE bankkaarten
                SET Code = %s
                WHERE KaartID = %s;
        """)
        self.cursor.execute(self.query, (code, id))

    def close(self):
        self.cursor.close()
        self.cnx.close()

RFid()
