# import lcd160cr
# import pyb

# Use following to test for broken hardware - will spam random sqs on screen
import pyb
from lcd160cr import *

from Message import *
from Formats import *

lcd = None


def rgb(r, g, b):
    return LCD160CR.rgb(r, g, b)


def drawSquares():
    # lcd = LCD160CR('X')
    from random import randint
    for i in range(1000):
        fg = rgb(randint(128, 255), randint(128, 255), randint(128, 255))
        bg = rgb(randint(0, 128), randint(0, 128), randint(0, 128))
        lcd.set_pen(fg, bg)
        lcd.rect(randint(0, lcd.w), randint(0, lcd.h), randint(10, 40), randint(10, 40))

def resetPen():
    lcd.set_pos(0, 0)
    lcd.set_font(1, 0)
    lcd.set_scroll(False)
    lcd.set_text_color(lcd.rgb(255, 255, 255), lcd.rgb(0, 0, 0))

def initLCD():
    global lcd
    lcd = LCD160CR('X')
    lcd.set_pen(lcd.rgb(255, 255, 255), lcd.rgb(0, 0, 0))
    lcd.erase()
    resetPen()
    # lcd.write("LCD initiated")
    # for i in range(0, 20):
    #     lcd.write(str(i) + "\n")
    return lcd


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
    whiteText()
    changePenColour(rgb(255, 255, 255))
    clearScreen()
    resetPenPos()


def changeTextColour(fg, bg=rgb(0, 0, 0)):
    lcd.set_text_color(fg, bg)
    return fg, bg


def changeTextColourRGBNoBG(r, g, b):
    return changeTextColour(rgb(r, g, b), rgb(0, 0, 0))


def whiteText():
    changeTextColourRGBNoBG(255, 255, 255)


def changePenColour(line, fill=rgb(0, 0, 0)):
    lcd.set_pen(line, fill)
    return line, fill


def resetPenPos():
    lcd.set_pos(0, 0)


def showLLHStatus(fixOK, diffSol, tow, towValid, fixType, solValid, lat, lathp, lon, lonhp, h, hmsl, vAcc, hAcc,
                  datetime):
    resetLCD()
    if not towValid:
        changeTextColourRGBNoBG(255, 0, 0)
    writeLine("TOW:" + str(tow))

    whiteText()

    if not fixOK:
        changeTextColourRGBNoBG(255, 0, 0)
    writeLine("fix:" + str(fixType))

    if diffSol:
        writeToScreen("-Diff")

    whiteText()

    if not solValid:
        changeTextColourRGBNoBG(255, 0, 0)

    writeLine("lat:" + str(lat))
    writeLine("lathp:" + str(lathp))
    writeLine("lon:" + str(lon))
    writeLine("lon:" + str(lonhp))
    writeLine("height:" + str(h))
    writeLine("hmsl:" + str(hmsl))
    writeLine("hAcc:" + str(hAcc))
    writeLine("vAcc:" + str(vAcc))
    writeLine("----------------")
    writeLine("date: " + str(datetime.getDateString()))
    writeLine("time: " + str(datetime.getTimeString()))


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


def showSVINStatus(svinmsg):
    if svinmsg is None:
        svinmsg = SVIN(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    resetLCD()
    if svinmsg.active == 1:
        changeTextColourRGBNoBG(0, 255, 0)
        writeLine("Status: In progress")
    else:
        changeTextColourRGBNoBG(255, 0, 0)
        writeLine("Status: Inactive")

    writeLine("Observation time: " + str(svinmsg.dur))
    if svinmsg.valid == 1:
        changeTextColourRGBNoBG(0, 255, 0)
    else:
        changeTextColourRGBNoBG(255, 0, 0)

    writeLine("X: " + str((svinmsg.meanX + .01 * svinmsg.meanXHp) * .01))
    writeLine("Y: " + str((svinmsg.meanY + .01 * svinmsg.meanYHp) * .01))
    writeLine("Z: " + str((svinmsg.meanZ + .01 * svinmsg.meanZHp) * .01))
    writeLine("Mean Acc: " + str(svinmsg.meanAcc * .0001))
    writeLine("Positions used: " + str(svinmsg.obs))


def triggerSVIN():
    bs = bytearray()
    bs.append(0xb5)
    bs.append(0x62)
    bs.append(0x06)
    bs.append(0x71)
    bs.append(0x28)
    bs.append(0)

    bs.append(0)
    bs.append(0)
    bs.append(1)
    bs.append(0)

    for i in range(20):
        bs.append(0)
    bs.append(0x58)
    bs.append(0x02)
    bs.append(0)
    bs.append(0)

    bs.append(0xe8)
    bs.append(0x03)
    bs.append(0)
    bs.append(0)
    for i in range(8):
        bs.append(0)

    ck_a, ck_b = ubxChecksum(bs[2:])
    bs.append(ck_a)
    bs.append(ck_b)

    return bs

def initLCDAPI():
    initLCD()

pages = []
page = 0
powered = 1
UPDATE_TIME = 1000
updateIn = UPDATE_TIME


def updateLCD(delay):
    global pages, page, updateIn, UPDATE_TIME
    if powered == 0:
        return
    elif updateIn <= 0:
        updateIn = UPDATE_TIME
        clearScreen()
        resetPen()
        pages[page].drawWidgets()
    else:
        updateIn -= delay

def togglePower():
    global powered
    powered = 1 - powered
    lcd.set_power(powered)

def drawPage():
    global powered, pages, page
    if powered == 1:
        resetPen()
        pages[page].drawWidgets()

def forceDrawPage(page):
    if powered == 1:
        clearScreen()
        resetPen()
        page.drawWidgets()

def leftPage():
    global pages, page
    page -= 1
    if page < 0:
        page = len(pages)
    forceDrawPage(pages[page])

def rightPage():
    global pages, page
    page += 1
    if page >= len(pages):
        page = 0
    forceDrawPage(pages[page])

def getLRButtons():
    ltriange, rtriangle = getLRTriangles()
    rbutton = RectButton(llims=(90, 122), ulims=(120, 152), outlineColour=rgb(48, 48, 48), fillColour=rgb(199, 199, 199),
                      filled=True, detail=[rtriangle], callback=rightPage)
    lbutton = RectButton(llims=(8, 122), ulims=(38, 152), outlineColour=rgb(48, 48, 48), fillColour=rgb(199, 199, 199),
                       filled=True, detail=[ltriangle], callback=leftPage)
    return lbutton, rbutton

def getBusyScreen():
    global lcd
    title = TextLine("WARNING", 19, 10, size=2)
    line1 = TextLine("Reading", 19, 30, size=2)
    line2 = TextLine("in", 19, 50, size=2)
    line3 = TextLine("progress", 19, 70, size=2)
    busyscreen = Screen(lcd, widgets=[title, line1, line2, line3])
    return busyscreen

def getLRTriangles():
    rtriangle = bytearray()
    rtriangle.extend(bytes([100, 132]))
    rtriangle.extend(bytes([100, 142]))
    rtriangle.extend(bytes([110, 137]))
    rtriangle.extend(bytes([100, 132]))

    ltriangle = bytearray()
    ltriangle.extend(bytes([28, 132]))
    ltriangle.extend(bytes([28, 142]))
    ltriangle.extend(bytes([18, 137]))
    ltriangle.extend(bytes([28, 132]))
    return ltriangle, rtriangle

def checkTouches():
    global pages, page
    if powered == 1:
        touches = pages[page].getTouches()
        if len(touches) > 0:
            touch = touches[0]
            touch.callback()

class Screen:
    widgets = None
    penFg = None
    penBg = None
    screen = None

    def __init__(self, screen, penFg=rgb(255, 255, 255), penBg=rgb(0, 0, 0), widgets=None):
        if widgets is None:
            widgets = []
        self.screen = screen
        self.penFg = penFg
        self.penBg = penBg
        self.widgets = widgets

    # I'm assuming here that it could be multitouch, although I
    # don't know if the lcd16cr is...
    def getTouches(self):
        touches = []
        for w in self.widgets:
            if w.is_touched():
                touches.append(w)
        return touches

    def drawWidgets(self):
        for w in self.widgets:
            w.draw()

    def eraseScreen(self):
        self.screen.erase()


class Widget:
    name = "default widget"
    x_u_lim, y_u_lim, x_l_lim, y_l_lim = 0, 0, 0, 0
    lcd = None

    callback = None

    def __init__(self, llims=(0, 0), ulims=(0, 0), callback=None):
        self.callback = callback
        self.x_l_lim, self.y_l_lim = llims
        self.x_u_lim, self.y_u_lim = ulims

    def draw(self):
        pass

    def is_touched(self):
        return False

    def is_touched_action(self):
        return self.callback

    def toString(self):
        return self.name


class RectButton(Widget):
    filled = False
    outlineCol = None
    fillCol = None

    detail = []

    def __init__(self, llims=(0, 0), ulims=(0, 0), fillColour=rgb(0, 0, 0), outlineColour=rgb(255, 255, 255),
                 filled=False,
                 detail=None, callback=(lambda: print("RectButton pressed"))):

        if detail is None:
            detail = [bytearray()]
        self.detail = detail

        print(callback)
        callback()

        self.fillCol = fillColour
        self.outlineCol = outlineColour
        self.filled = filled
        super(RectButton, self).__init__(llims=llims, ulims=ulims, callback=callback)
        print(self.x_u_lim, self.x_l_lim)
        print(self.y_u_lim, self.y_l_lim)
        self.name = "RectButton at [" + str((self.x_l_lim, self.y_l_lim)) + ", " + str(
            (self.x_u_lim, self.y_u_lim)) + "]"

    def draw(self):
        lcd.set_pen(self.outlineCol, self.fillCol)
        if self.filled:
            lcd.rect_interior(self.x_l_lim, self.y_l_lim, (self.x_u_lim - self.x_l_lim), (self.y_u_lim - self.y_l_lim))
        else:
            lcd.rect_outline(self.x_l_lim, self.y_l_lim, (self.x_u_lim - self.x_l_lim), (self.y_u_lim - self.y_l_lim))

        if self.detail is not None:
            print(self.detail)
            for shape in self.detail:
                lcd.poly_line(shape)

    def is_touched(self):
        active, touchx, touchy = lcd.get_touch()
        if active == 1 \
                and self.x_l_lim < touchx < self.x_u_lim \
                and self.y_l_lim < touchy < self.y_u_lim:
            return True

    def addDetailPoint(self, pointX, pointY):
        self.detail.extend(bytes([pointX, pointY]))

# AAAH lost in hard reset, need to reimplement
class TextLine(Widget):
    fgcol = None
    bgcol = None
    text = None
    xpos=0
    ypos=0
    size=0
    font=0

    def __init__(self, text, xpos, ypos, fg=rgb(0,0,0), bg=rgb(255,255,255), size=1, font=1):
        self.xpos = xpos
        self.ypos = ypos
        self.text = text
        self.fgcol = fg
        self.bgcol = bg
        self.font = font
        self.size = size

    def draw(self):
        lcd.set_pos(self.xpos, self.ypos)
        lcd.set_font(self.font, self.scale)
        lcd.set_text_color(self.fgcol, self.bgcol)
        lcd.write(self.text)
