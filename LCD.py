# import lcd160cr
# import pyb

# Use following to test for broken hardware - will spam random sqs on screen
import pyb
import lcd160cr

lcd = None


def drawSquares():
    lcd = lcd160cr.LCD160CR('X')
    from random import randint
    for i in range(1000):
        fg = lcd.rgb(randint(128, 255), randint(128, 255), randint(128, 255))
        bg = lcd.rgb(randint(0, 128), randint(0, 128), randint(0, 128))
        lcd.set_pen(fg, bg)
        lcd.rect(randint(0, lcd.w), randint(0, lcd.h), randint(10, 40), randint(10, 40))


def initLCD():
    global lcd
    lcd = lcd160cr.LCD160CR('X')
    lcd.erase()
    lcd.set_pen(lcd.rgb(255, 255, 255), lcd.rgb(0, 0, 0))
    lcd.set_pos(0, 0)
    lcd.set_font(1, 0)
    lcd.set_scroll(False)
    lcd.set_text_color(lcd.rgb(255, 255, 255), lcd.rgb(0, 0, 0))
    # lcd.write("LCD initiated")
    # for i in range(0, 20):
    #     lcd.write(str(i) + "\n")


def writeToScreen(text):
    lcd.write(text)


def writeLine(text):
    lcd.write(text + "\n\r")


def clearScreen():
    lcd.erase()


def showArgs(**kwargs):
    clearScreen()
    lcd.set_pos(0, 0)
    for key, value in kwargs.items():
        writeLine("%s: %s" % (key, value))


def resetLCD():
    clearScreen()
    resetPenPos()
    changePenColour(lcd.rgb(255, 255, 255), lcd.rgb(0, 0, 0))


def changePenColour(fg, bg):
    lcd.set_text_color(fg, bg)


def changePenColourRGBNoBG(r, g, b):
    changePenColour(lcd.rgb(r, g, b), lcd.rgb(0, 0, 0))


def whiteText():
    changePenColourRGBNoBG(255, 255, 255)


def resetPenPos():
    lcd.set_pos(0, 0)


def showLLHStatus(fixOK, diffSol, tow, towValid, fixType, solValid, lat, lathp, lon, lonhp, h, hmsl, vAcc, hAcc, datetime):
    resetLCD()
    if not towValid:
        changePenColourRGBNoBG(255, 0, 0)
    writeLine("TOW:" + str(tow))

    whiteText()

    if not fixOK:
        changePenColourRGBNoBG(255, 0, 0)
    writeLine("fix:" + str(fixType))

    if diffSol:
        writeToScreen("-Diff")

    whiteText()

    if not solValid:
        changePenColourRGBNoBG(255, 0, 0)

    writeLine("lat:" + str(lat))
    writeLine("lathp:" + str(lathp))
    writeLine("lon:" + str(lon))
    writeLine("lon:" + str(lonhp))
    writeLine("height:" + str(h))
    writeLine("hmsl:" + str(hmsl))
    writeLine("hAcc:" + str(hAcc))
    writeLine("vAcc:" + str(vAcc))
    writeLine("----------------")
    writeLine("date: "+str(datetime.getDateString()))
    writeLine("time: "+str(datetime.getTimeString()))


def showStatus(xPos, yPos, zPos, pAcc, lat, lon, lathp, lonhp, h, sats, fix):
    resetLCD()
    writeLine("xPos:" + str(xPos))
    writeLine("yPos:" + str(yPos))
    writeLine("zPos:" + str(zPos))
    writeLine("pAcc:" + str(pAcc))
    writeLine("lat:" + str(lat))
    writeLine("lathp:" + str(lathp))
    writeLine("lon:" + str(lon))
    writeLine("lonhp:" + str(lonhp))
    writeLine("height:" + str(h))
    writeLine("sats:" + str(sats))
    writeLine("fix:" + str(fix))
