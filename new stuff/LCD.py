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
    lcd.set_pen(rgb(255, 255, 255), rgb(0, 0, 0))


def initLCD():
    global lcd
    lcd = LCD160CR('X')
    lcd.set_orient(LANDSCAPE_UPSIDEDOWN)
    lcd.set_pen(lcd.rgb(255, 255, 255), lcd.rgb(0, 0, 0))
    lcd.erase()
    resetPen()
    # lcd.save_to_flash()
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


def initLCDAPI(log_freq=0, log_start=0, keep_raw=False, keep_med=False, keep_best=False, baseStation=True, svin_dur=0,
               svin_acc=0, svintrigger=lambda: print()):
    global pages, powered, lcd, svinpage, locpage
    initLCD()
    # lcd.save_to_flash()
    setupPowerButton()
    pages.append(getSettingsScreen(log_freq, log_start, keep_raw, keep_med, keep_best))
    if baseStation:
        print(baseStation, "==> added")
        pages.append(getSVINSettingsScreen(svin_dur, svin_acc, svintrigger))
        svinpage = len(pages)
        pages.append(getSVINMonitorScreen())

    locpage = len(pages)
    pages.append(getLocMonitorScreen())


pages = []
page = 0
powered = 1
UPDATE_TIME = 500 # ms before LCD updates on-screen info
updateIn = 0 # force draw on startup


def updateLCD(delay):
    global pages, page, updateIn, UPDATE_TIME, reading
    page_ = pages[page]
    if powered == 0 or reading:
        return
    elif updateIn <= 0:
        updateIn = UPDATE_TIME
        resetPen()
        page_.eraseScreen()
        page_.drawWidgets()
    else:
        updateIn -= delay
    touches = page_.getTouches()
    if len(touches) > 0:
        touches[0].callback()


def setupPowerButton():
    b = pyb.Switch()
    b.callback(togglePower)


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
    global pages, page, powered
    print("Changing page - L")
    if len(pages) == 0 or powered == 0:
        print("No pages or unpowered:", len(pages), powered)
        return
    page -= 1
    if page < 0:
        page = len(pages) - 1
    forceDrawPage(pages[page])


def rightPage():
    global pages, page, powered
    print("Changing page - R")
    if len(pages) == 0 or powered == 0:
        print("No pages or unpowered:", len(pages), powered)
        return
    page += 1
    if page >= len(pages):
        page = 0
    forceDrawPage(pages[page])


lbutton, rbutton = (None, None)


def getLRButtons():
    global lbutton, rbutton
    if lbutton is not None and rbutton is not None:
        return lbutton, rbutton

    ltriangle, rtriangle = getLRTriangles()
    rbutton = RectButton(llims=(135, 5), ulims=(155, 25), outlineColour=rgb(48, 48, 48),
                         fillColour=rgb(199, 199, 199),
                         filled=True, detail=[rtriangle], callback=rightPage)
    lbutton = RectButton(llims=(135, 103), ulims=(155, 123), outlineColour=rgb(48, 48, 48),
                         fillColour=rgb(199, 199, 199),
                         filled=True, detail=[ltriangle], callback=leftPage)
    return lbutton, rbutton


def getBusyScreen():
    global lcd
    title = TextLine("WARNING", 19, 10, size=0, font=3)
    line1 = TextLine("Logging", 19, 30, size=0, font=3)
    line2 = TextLine("in", 19, 50, size=0, font=3)
    line3 = TextLine("progress", 19, 70, size=0, font=3)
    busyscreen = Screen(lcd, widgets=[title, line1, line2, line3])
    return busyscreen


reading = False
def makeLCDBusy():
    global reading
    reading = True
    forceDrawPage(getBusyScreen())

def makeLCDFree():
    global reading
    reading = False

def getLRTriangles():
    rtriangle = bytearray()
    rtriangle.extend(bytes([141, 19]))
    rtriangle.extend(bytes([145, 11]))
    rtriangle.extend(bytes([149, 19]))
    rtriangle.extend(bytes([141, 19]))

    ltriangle = bytearray()
    ltriangle.extend(bytes([141, 109]))
    ltriangle.extend(bytes([145, 117]))
    ltriangle.extend(bytes([149, 109]))
    ltriangle.extend(bytes([141, 109]))
    return ltriangle, rtriangle


def checkTouches():
    global pages, page
    if powered == 1:
        touches = pages[page].getTouches()
        if len(touches) > 0:
            touch = touches[0]
            touch.callback()

def getPrintableDate():
    year, month, day, weekday, hours, minutes, seconds, subseconds = pyb.RTC().datetime()
    return str(day) + "/" + str(month) + "/" + str(year)

def getPrintableTime():
    year, month, day, weekday, hours, minutes, seconds, subseconds = pyb.RTC().datetime()
    return str(hours)+":"+str(minutes)+":"+str(seconds)+"."+str(subseconds)

def getSettingsScreen(log_freq, log_start, keep_raw, keep_med, keep_best):
    global lcd
    title = TextLine("SETTINGS", 10, 10, size=0, font=3)
    date_line = TextLine(getPrintableDate(), 10, 25, size=0, font=2, fg=rgb(10, 100, 200), update=getPrintableDate)
    time_line = TextLine(getPrintableTime(), 10, 33, size=0, font=2, fg=rgb(10, 100, 200), update=getPrintableTime)
    log_freq_line = TextLine("Log every: " + "{0:.2f}h".format(log_freq * 1e-3 / 60**2), 10, 46, size=0, font=3)
    log_start_line = TextLine("Log start: " + str(log_start), 10, 58, size=0, font=3)
    keep_raw_line = TextLine("Keep Raw", 10, 70, size=0, font=3,
                             fg=rgb(0 if keep_raw else 255, 255 if keep_raw else 0, 0))
    keep_med_line = TextLine("Keep Median", 10, 82, size=0, font=3,
                             fg=rgb(0 if keep_med else 255, 255 if keep_med else 0, 0))
    keep_best_line = TextLine("Keep Best", 10, 94, size=0, font=3,
                              fg=rgb(0 if keep_best else 255, 255 if keep_best else 0, 0))
    lbutton, rbutton = getLRButtons()
    widgets = [lbutton, rbutton, title, log_freq_line, log_start_line, keep_raw_line, keep_med_line, keep_best_line, date_line, time_line]

    if not keep_raw:
        strike2 = Line((8, 75), (112, 75), col=rgb(255, 0, 0))
        widgets.append(strike2)
    if not keep_med:
        strike3 = Line((8, 87), (112, 87), col=rgb(255, 0, 0))
        widgets.append(strike3)
    if not keep_best:
        strike1 = Line((8, 99), (112, 99), col=rgb(255, 0, 0))
        widgets.append(strike1)
    screen = Screen(lcd, widgets=widgets)
    return screen


def getSVINSettingsScreen(svin_dur, svin_acc, svintrigger):
    global lcd
    title = TextLine("SVIN SETTINGS", 10, 10, size=0, font=3)
    duration_line = TextLine("Min. duration: " + str(svin_dur), 10, 32, size=0, font=3)
    acc_line = TextLine("Min. acc: " + str(svin_acc), 10, 44, size=0, font=3)
    triggerLine = TextLine("TRIGGER", 35, 75, size=0, font=3)
    triggerBox = RectButton(llims=(10, 64), ulims=(128, 96), filled=False, outlineColour=rgb(255, 279, 102),
                            callback=svintrigger, detail=[triggerLine])
    lbutton, rbutton = getLRButtons()
    screen = Screen(lcd, widgets=[lbutton, rbutton, title, duration_line, acc_line, triggerBox])
    return screen


monitoring = True
def startMonitoring():
    global monitoring, powered
    monitoring = True and powered == 1 # don't monitor when LCD unpowered

def stopMonitoring():
    global monitoring
    monitoring = False


svindata = None
svinpage = -1
def getSVINMonitorScreen():
    global lcd, svindata
    title = TextLine("SVIN MONITOR", 10, 10, size=0, font=3)
    lbutton, rbutton = getLRButtons()
    if svindata is not None:
        x_line = TextLine("X: " + str(svindata.getXPos()), 10, 32, size=0, font=3)
        y_line = TextLine("Y: " + str(svindata.getYPos()), 10, 44, size=0, font=3)
        z_line = TextLine("Z: " + str(svindata.getZPos()), 10, 56, size=0, font=3)
        acc_line = TextLine("Acc.: " + str(svindata.getPAcc()), 10, 68, size=0, font=3)
        duration_line = TextLine("Duration: " + str(svindata.getDuration()), 10, 80, size=0, font=3)
        screen = Screen(lcd, widgets=[lbutton, rbutton, title, x_line, y_line, z_line, acc_line, duration_line])
    else:
        warning_line = TextLine("NO DATA", 20, 60, size=0, font=3, fg=rgb(255, 85, 0))
        screen = Screen(lcd, widgets=[lbutton, rbutton, title, warning_line])

    return screen


def updateSVINMonitorData(svinmsg):
    global svindata, svinpage
    svindata = svinmsg
    noPreviousData = svindata is None
    print(svindata, "not none?")
    # print(svs, satellites)
    svindata = svinmsg
    if noPreviousData:
        remakeScreen(svinpage, getSVINMonitorScreen())  # remakes Screen obj with new data - changes "NO DATA" to monitor

locdata = None
satellites = 0
locpage = -1
def getLocMonitorScreen():
    global lcd, locdata, satellites
    title = TextLine("LOC MONITOR", 10, 10, size=0, font=3)
    lbutton, rbutton = getLRButtons()
    if locdata is not None:
        print(locdata,"should not be none")
        col = rgb(255, 85, 0) if locdata.invalidFix else rgb(255,255,255)
        x_line = TextLine("X: " + str(locdata.getXPos()), 10, 32, size=0, font=2, fg=col, update=lambda:"X: " + str(locdata.getXPos()))
        y_line = TextLine("Y: " + str(locdata.getYPos()), 10, 44, size=0, font=2, fg=col, update=lambda:"Y: " + str(locdata.getYPos()))
        z_line = TextLine("Z: " + str(locdata.getZPos()), 10, 56, size=0, font=2, fg=col, update=lambda:"Z: " + str(locdata.getZPos()))
        acc_line = TextLine("Acc.: " + str(locdata.getPAcc())+"m", 10, 68, size=0, font=2, fg=col, update=lambda:"Acc.: " + str(locdata.getPAcc())+"m")
        satellites_line = TextLine("Satellites: " + str(satellites), 10, 80, size=0, font=2, fg=col, update=lambda:"Satellites: " + str(satellites))
        screen = Screen(lcd,
                        widgets=[lbutton, rbutton, title, x_line, y_line, z_line, acc_line, satellites_line])
    else:
        print("but for some reason it is")
        warning_line = TextLine("NO DATA", 20, 60, size=0, font=3, fg=rgb(255, 85, 0))
        screen = Screen(lcd, widgets=[lbutton, rbutton, title, warning_line])
    return screen


def updateLocMonitorData(locmsg, svs):
    global locdata, locpage, satellites
    noPreviousData = locdata
    satellites = svs
    print(svs, "not none? --- --- ")
    # print(svs, satellites)
    locdata = locmsg
    if noPreviousData:
        remakeScreen(locpage, getLocMonitorScreen()) # remakes Screen obj with new data - changes "NO DATA" to monitor


def remakeScreen(pageno, newscreen):
    global pages
    pages[pageno] = newscreen

pers_touch = False
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

    # I'm assuming here that it could be multitouch, although the LCD160CR isn't
    # single on-press response, no persistent touch
    def getTouches(self):
        global pers_touch
        # means if you hold down on the screen it registers as one touch
        touches = []
        for w in self.widgets:
            if w.is_touched():
                touches.append(w)

        # if touched last update and still touched then cancel touch registration
        if pers_touch and len(touches) > 0:
            return []
        else:
            pers_touch = len(touches) > 0
            return touches

        # if touched, return

    def drawWidgets(self):
        lcd.set_pen(self.penFg, self.penBg)
        for w in self.widgets:
            w.draw()

    def eraseScreen(self):
        lcd.set_pen(self.penFg, self.penBg)
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

    def __init__(self, llims=(0, 0), ulims=(0, 0), size=(0, 0), fillColour=rgb(0, 0, 0),
                 outlineColour=rgb(255, 255, 255),
                 filled=False,
                 detail=None, callback=(lambda: print("RectButton pressed"))):

        if detail is None:
            detail = [bytearray()]
        self.detail = detail

        # print(callback)
        # callback()

        self.fillCol = fillColour
        self.outlineCol = outlineColour
        self.filled = filled
        super(RectButton, self).__init__(llims=llims, ulims=ulims, callback=callback)
        # print(self.x_u_lim, self.x_l_lim)
        # print(self.y_u_lim, self.y_l_lim)
        self.name = "RectButton at [" + str((self.x_l_lim, self.y_l_lim)) + ", " + str(
            (self.x_u_lim, self.y_u_lim)) + "]"

    def draw(self):
        lcd.set_pen(self.outlineCol, self.fillCol)
        if self.filled:
            lcd.rect_interior(self.x_l_lim, self.y_l_lim, abs(self.x_u_lim - self.x_l_lim),
                              abs(self.y_u_lim - self.y_l_lim))
        else:
            lcd.rect_outline(self.x_l_lim, self.y_l_lim, abs(self.x_u_lim - self.x_l_lim),
                             abs(self.y_u_lim - self.y_l_lim))

        if self.detail is not None:
            # print(self.detail)
            for shape in self.detail:
                if issubclass(type(shape), Widget):
                    shape.draw()
                else:
                    lcd.poly_line(shape)

    def is_touched(self):
        active, touchx, touchy = lcd.get_touch()
        print(lcd.get_touch())
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
    xpos = 0
    ypos = 0
    size = 0
    font = 0
    update = None

    def __init__(self, text, xpos, ypos, fg=rgb(255, 255, 255), bg=rgb(0, 0, 0), size=1, font=1, update=None):
        self.xpos = xpos
        self.ypos = ypos
        self.text = text
        self.fgcol = fg
        self.bgcol = bg
        self.font = font
        self.size = size
        self.update = update

    def draw(self):
        if self.update is not None:
            self.updateText(self.update())
        lcd.set_pos(self.xpos, self.ypos)
        lcd.set_font(self.font, self.size)
        lcd.set_text_color(self.fgcol, self.bgcol)
        lcd.write(self.text)

    def updateText(self, updated):
        print("Updating display text to", updated)
        self.text = str(updated)

    def appendText(self, append):
        self.text += str(append)

    def prependText(self, prepend):
        self.text = str(prepend) + self.text


class Line(Widget):
    xStart = 0
    xEnd = 0
    yStart = 0
    yEnd = 0
    col = rgb(0, 0, 0)

    def __init__(self, start, end, col=rgb(255, 255, 255)):
        self.x_l_lim, self.y_l_lim = start
        self.x_u_lim, self.y_u_lim = end
        self.col = col

    def draw(self):
        lcd.set_pen(self.col, rgb(0, 0, 0))
        lcd.line(self.x_u_lim, self.y_u_lim, self.x_l_lim, self.y_l_lim)

    def is_touched(self):
        return False
